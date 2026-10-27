from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from accounts.permissions import is_root
from audit.models import AuditLog
from catalog.models import Product
from catalog.services import ensure_product_spec_placeholders
from comparison.models import ProductMatch
from core.permissions import contributor_required

from .forms import ChangeSubmissionForm, MatchAddForm
from .models import ChangeRequest
from .services import (
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
@require_GET
def edit_product_page(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk, is_published=True)
    return redirect(f'{reverse("product-detail", args=(product.pk,))}?edit=1')


def _save_benchmark(request, product, form):
    competitor, competitor_created = form.save_competitor(request.user)
    existing_matches = ProductMatch.objects.filter(
        our_product=product,
        competitor_product=competitor,
        region=product.region,
    )
    match = existing_matches.exclude(status=ProductMatch.Status.REJECTED).order_by(
        "-benchmark_case_id", "-updated_at", "-pk"
    ).first()
    if match is None:
        match = existing_matches.order_by("-benchmark_case_id", "-updated_at", "-pk").first()
    match_created = match is None
    if match_created:
        match = ProductMatch(
            our_product=product,
            competitor_product=competitor,
            benchmark_case=None,
            region=product.region,
            created_by=request.user,
        )
    match.match_type = form.cleaned_data["match_type"]
    match.match_level = form.cleaned_data["match_level"]
    match.status = ProductMatch.Status.CONFIRMED
    match.rank = form.cleaned_data.get("rank") or 0
    match.match_score = form.cleaned_data.get("match_score")
    match.confidence = form.cleaned_data.get("confidence")
    match.reason = form.cleaned_data.get("relation_reason", "")
    match.source_url = form.cleaned_data.get("source_url", "")
    match.updated_by = request.user
    match.save()
    AuditLog.objects.create(
        actor=request.user,
        action="benchmark.added" if match_created else "benchmark.restored",
        object_type=match._meta.label,
        object_id=str(match.pk),
        object_repr=str(match),
        before_data={"exists": not match_created},
        after_data={
            "status": match.status,
            "competitor_created": competitor_created,
            "competitor_visible": True,
        },
        ip_address=request_ip(request),
    )
    return competitor


@contributor_required
@require_http_methods(["GET", "POST"])
def edit_benchmarks(request, product_pk):
    product = get_object_or_404(
        Product.objects.filter(
            is_published=True,
            brand__is_own_brand=True,
        ).select_related("brand", "category", "product_type"),
        pk=product_pk,
    )
    action = request.POST.get("action", "") if request.method == "POST" else ""
    form = MatchAddForm(
        request.POST if action == "add_match" else None,
        request.FILES if action == "add_match" else None,
        product=product,
    )

    if request.method == "POST" and action.startswith("remove_match:"):
        match = get_object_or_404(
            ProductMatch.objects.select_related("competitor_product").filter(
                our_product=product,
            ).exclude(status=ProductMatch.Status.REJECTED),
            pk=action.partition(":")[2],
        )
        competitor = match.competitor_product
        with transaction.atomic():
            duplicate_matches = list(
                ProductMatch.objects.filter(
                    our_product=product,
                    competitor_product=competitor,
                ).exclude(status=ProductMatch.Status.REJECTED)
            )
            before_statuses = {duplicate.pk: duplicate.status for duplicate in duplicate_matches}
            for duplicate in duplicate_matches:
                duplicate.status = ProductMatch.Status.REJECTED
                duplicate.updated_by = request.user
                duplicate.save(update_fields=("status", "updated_by", "updated_at"))
            has_other_matches = competitor.matched_as_competitor.exclude(
                status=ProductMatch.Status.REJECTED
            ).exists()
            if not has_other_matches:
                competitor.is_published = False
                competitor.updated_by = request.user
                competitor.save(update_fields=("is_published", "updated_by", "updated_at"))
            for duplicate in duplicate_matches:
                AuditLog.objects.create(
                    actor=request.user,
                    action="benchmark.removed",
                    object_type=duplicate._meta.label,
                    object_id=str(duplicate.pk),
                    object_repr=str(duplicate),
                    before_data={"status": before_statuses[duplicate.pk], "competitor_visible": True},
                    after_data={"status": duplicate.status, "competitor_visible": has_other_matches},
                    ip_address=request_ip(request),
                )
        suffix = " The competitor was hidden because it has no other benchmarks." if not has_other_matches else ""
        messages.success(request, "Benchmark removed." + suffix)
        return redirect("changes:edit-benchmarks", product_pk=product.pk)

    if request.method == "POST" and action == "add_match" and form.is_valid():
        with transaction.atomic():
            competitor = _save_benchmark(request, product, form)
        messages.success(request, "Benchmark added. Complete the competitor specifications below.")
        return redirect(f'{reverse("product-detail", args=(competitor.pk,))}?edit=1')

    match_queryset = product.competitor_matches.exclude(
        status=ProductMatch.Status.REJECTED
    ).select_related("competitor_product__brand").order_by(
        "competitor_product_id", "-benchmark_case_id", "-updated_at", "-pk"
    )
    matches_by_product = {}
    for match in match_queryset:
        matches_by_product.setdefault(match.competitor_product_id, match)
    matches = sorted(
        matches_by_product.values(),
        key=lambda match: (
            match.rank,
            match.competitor_product.brand.name.casefold(),
            match.competitor_product.model.casefold(),
        ),
    )
    return render(
        request,
        "changes/edit_benchmarks.html",
        {"product": product, "matches": matches, "form": form},
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

    if request.method == "POST":
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
