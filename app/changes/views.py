from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from accounts.permissions import is_root
from catalog.models import Product
from catalog.services import ensure_product_spec_placeholders
from core.permissions import contributor_required

from .forms import ChangeSubmissionForm, MatchAddForm, ProductPageEditForm
from .models import ChangeRequest
from .services import (
    MATCH_ADD_FIELD,
    apply_change,
    build_target_options,
    display_snapshot,
    proposed_value_hint,
    request_ip,
    resolve_target,
    snapshot_for_selection,
)


def _change_queryset():
    return ChangeRequest.objects.select_related(
        "target_product__brand",
        "target_spec__definition",
        "target_match__competitor_product__brand",
        "submitted_by",
        "reviewed_by",
    )


def _submit_change(request, attributes):
    with transaction.atomic():
        change = ChangeRequest.objects.create(**attributes)
        apply_change(
            change.pk,
            request.user,
            "Applied automatically; approval is not required.",
            request_ip(request),
        )
    return change


@contributor_required
@require_http_methods(["GET", "POST"])
def edit_product_page(request, product_pk):
    product = get_object_or_404(
        Product.objects.select_related("brand", "category", "product_type"),
        pk=product_pk,
        is_published=True,
    )
    ensure_product_spec_placeholders(product)
    form = ProductPageEditForm(
        request.POST or None,
        product=product,
    )
    if request.method == "POST" and form.is_valid():
        try:
            changed_values = form.changed_values()
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            with transaction.atomic():
                for selection, old_value, proposed_value in changed_values:
                    attributes = {
                        "request_type": selection["request_type"],
                        "target_product": product,
                        "field_name": selection["field_name"],
                        "old_value": old_value,
                        "proposed_value": proposed_value,
                        "reason": "Edited directly from the product page.",
                        "submitted_by": request.user,
                    }
                    if selection["request_type"] == ChangeRequest.RequestType.SPEC:
                        attributes["target_spec"] = selection["target"]
                        attributes["source_url"] = (
                            selection["target"].source_url or product.official_url
                        )
                    _submit_change(request, attributes)
            if changed_values:
                messages.success(
                    request,
                    f"Saved {len(changed_values)} change(s).",
                )
            else:
                messages.info(request, "No changes were made.")
            return redirect("product-detail", pk=product.pk)

    grouped_fields = []
    for item in form.edit_items:
        if not grouped_fields or grouped_fields[-1]["name"] != item["group"]:
            grouped_fields.append({"name": item["group"], "items": []})
        grouped_fields[-1]["items"].append(
            {
                **item,
                "field": form[item["name"]],
            }
        )
    return render(
        request,
        "changes/edit_product.html",
        {
            "product": product,
            "form": form,
            "grouped_fields": grouped_fields,
        },
    )


@contributor_required
@require_http_methods(["GET", "POST"])
def suggest_change(request, product_pk):
    product = get_object_or_404(
        Product.objects.filter(is_published=True).select_related("brand", "category"),
        pk=product_pk,
    )
    ensure_product_spec_placeholders(product)
    target_options = build_target_options(product)
    if not target_options:
        raise Http404("No editable fields are available.")
    target_key = request.POST.get("target") or request.GET.get("target") or target_options[0]["key"]
    try:
        selection = resolve_target(product, target_key)
    except ValidationError as exc:
        raise Http404(str(exc)) from exc

    adding_match = request.method == "POST" and request.POST.get("action") == "add_match"
    add_match_form = MatchAddForm(
        request.POST if adding_match else None,
        request.FILES if adding_match else None,
        product=product,
    )

    if adding_match:
        if not product.brand.is_own_brand:
            raise Http404("Only own-brand products can have competitor matches.")
        if add_match_form.is_valid():
            competitor = add_match_form.cleaned_data["competitor_product"]
            benchmark_case = (
                product.benchmark_cases.filter(region=product.region)
                .order_by("-status", "pk")
                .first()
            )
            region = benchmark_case.region if benchmark_case else product.region
            proposed = {
                "competitor_product_id": competitor.pk,
                "benchmark_case_id": benchmark_case.pk if benchmark_case else None,
                "region": region,
                "match_type": add_match_form.cleaned_data["match_type"],
                "match_level": add_match_form.cleaned_data["match_level"],
                "rank": add_match_form.cleaned_data["rank"],
                "match_score": add_match_form.cleaned_data["match_score"],
                "confidence": add_match_form.cleaned_data["confidence"],
                "reason": add_match_form.cleaned_data["relation_reason"],
                "source_url": add_match_form.cleaned_data["source_url"],
            }
            change = _submit_change(
                request,
                {
                    "request_type": ChangeRequest.RequestType.MATCH,
                    "target_product": product,
                    "field_name": MATCH_ADD_FIELD,
                    "old_value": {"exists": False},
                    "proposed_value": proposed,
                    "reason": add_match_form.cleaned_data["request_reason"],
                    "source_url": add_match_form.cleaned_data["source_url"],
                    "attachment": add_match_form.cleaned_data["attachment"],
                    "submitted_by": request.user,
                },
            )
            messages.success(request, "Benchmark added and saved.")
            return redirect("changes:detail", pk=change.pk)
        form = ChangeSubmissionForm(selection=selection)
    elif request.method == "POST":
        form = ChangeSubmissionForm(
            request.POST,
            request.FILES,
            selection=selection,
        )
        if form.is_valid():
            target = selection["target"]
            attributes = {
                "request_type": selection["request_type"],
                "target_product": product,
                "field_name": selection["field_name"],
                "old_value": form.cleaned_data["old_value"],
                "proposed_value": form.cleaned_data["parsed_proposed_value"],
                "reason": form.cleaned_data["reason"],
                "source_url": form.cleaned_data["source_url"],
                "attachment": form.cleaned_data["attachment"],
                "submitted_by": request.user,
            }
            if selection["request_type"] == ChangeRequest.RequestType.SPEC:
                attributes["target_spec"] = target
            elif selection["request_type"] == ChangeRequest.RequestType.MATCH:
                attributes["target_match"] = target
                attributes["target_product"] = target.our_product
            change = _submit_change(request, attributes)
            messages.success(request, "Change saved successfully.")
            return redirect("changes:detail", pk=change.pk)
    else:
        form = ChangeSubmissionForm(selection=selection)

    return render(
        request,
        "changes/suggest.html",
        {
            "product": product,
            "target_options": target_options,
            "target_key": target_key,
            "selection": selection,
            "current_value": display_snapshot(snapshot_for_selection(selection)),
            "value_hint": proposed_value_hint(selection),
            "form": form,
            "add_match_form": add_match_form,
        },
    )


@contributor_required
@require_GET
def my_changes(request):
    queryset = _change_queryset().filter(submitted_by=request.user)
    status = request.GET.get("status", "").strip()
    if status in ChangeRequest.Status.values:
        queryset = queryset.filter(status=status)
    page_obj = Paginator(queryset, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "changes/mine.html",
        {"page_obj": page_obj, "status": status, "status_choices": ChangeRequest.Status.choices},
    )


@login_required
@require_GET
def change_detail(request, pk):
    change = get_object_or_404(_change_queryset(), pk=pk)
    if not is_root(request.user) and change.submitted_by_id != request.user.pk:
        raise PermissionDenied
    return render(
        request,
        "changes/detail.html",
        {
            "change": change,
            "old_display": display_snapshot(change.old_value),
            "proposed_display": display_snapshot(change.proposed_value),
        },
    )


@login_required
@require_GET
def change_attachment(request, pk):
    change = get_object_or_404(ChangeRequest, pk=pk)
    if not is_root(request.user) and change.submitted_by_id != request.user.pk:
        raise PermissionDenied
    if not change.attachment:
        raise Http404
    suffix = Path(change.attachment.name).suffix.lower()
    return FileResponse(
        change.attachment.open("rb"),
        as_attachment=True,
        filename=f"change-{change.pk}-evidence{suffix}",
    )
