from datetime import date
from decimal import Decimal, InvalidOperation
from ipaddress import ip_address

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from audit.models import AuditLog
from catalog.models import Product, ProductSpec
from comparison.models import ProductMatch

from .models import ChangeRequest

PRODUCT_FIELDS = {
    "region": "Region",
    "hardware_version": "Hardware Version",
    "sku": "SKU",
    "lifecycle_status": "Lifecycle Status",
    "official_url": "Official URL",
    "datasheet_url": "Datasheet URL",
    "launch_date": "Launch Date",
    "notes": "Notes",
}
CATEGORY_PRODUCT_FIELDS = {
    "access-point": {
        "ap_type": "AP Type",
        "wifi_standard": "Wi-Fi Standard",
    },
    "wireless-bridge": {
        "ap_type": "Form Factor",
        "wifi_standard": "Wi-Fi Standard",
    },
}
MATCH_FIELDS = {
    "match_type": "Match Type",
    "match_level": "Match Level",
    "status": "Status",
    "match_score": "Match Score",
    "rank": "Rank",
    "confidence": "Confidence",
    "reason": "Match Reason",
    "advantages": "Advantages",
    "disadvantages": "Disadvantages",
    "source_url": "Match Source URL",
    "valid_from": "Valid From",
    "valid_to": "Valid To",
}
MATCH_DELETE_FIELD = "__delete__"
MATCH_ADD_FIELD = "__add__"


class ApprovalConflict(Exception):
    pass


def request_ip(request):
    value = request.META.get("REMOTE_ADDR", "").strip()
    try:
        return str(ip_address(value)) if value else None
    except ValueError:
        return None


def _number_string(value):
    if value is None:
        return None
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def snapshot_for_selection(selection):
    target = selection["target"]
    if selection["request_type"] == ChangeRequest.RequestType.SPEC:
        if target.value_status != ProductSpec.ValueStatus.PUBLISHED:
            return {"value_status": target.value_status}
        if target.definition.data_type == "boolean":
            return {"value_boolean": target.value_boolean}
        return {
            "value_text": target.value_text,
            "value_number": _number_string(target.value_number),
        }
    if (
        selection["request_type"] == ChangeRequest.RequestType.MATCH
        and selection["field_name"] == MATCH_DELETE_FIELD
    ):
        return {
            "competitor_product_id": target.competitor_product_id,
            "match_type": target.match_type,
            "match_level": target.match_level,
            "status": target.status,
            "region": target.region,
            "rank": target.rank,
        }
    value = getattr(target, selection["field_name"])
    if isinstance(value, date):
        value = value.isoformat()
    return {"value": value}


def display_snapshot(snapshot):
    if "delete" in snapshot:
        value = "删除对标关系"
    elif "exists" in snapshot:
        value = "已存在" if snapshot["exists"] else "尚未添加"
    elif "competitor_product_id" in snapshot and "match_type" in snapshot:
        value = (
            f"竞品 #{snapshot['competitor_product_id']} · "
            f"{snapshot['match_type']} · "
            f"{snapshot.get('match_level', '')}"
        )
    elif "value" in snapshot:
        value = snapshot["value"]
    elif "value_boolean" in snapshot:
        value = snapshot["value_boolean"]
    elif "value_status" in snapshot:
        value = dict(ProductSpec.ValueStatus.choices).get(
            snapshot["value_status"],
            snapshot["value_status"],
        )
    elif snapshot.get("value_number") is not None:
        value = snapshot["value_number"]
    else:
        value = snapshot.get("value_text", "")
    if value in (None, ""):
        return "Unknown"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def editable_product_fields(product):
    fields = dict(PRODUCT_FIELDS)
    fields.update(CATEGORY_PRODUCT_FIELDS.get(product.category.slug, {}))
    return fields


def build_target_options(product):
    options = []
    for field_name, label in editable_product_fields(product).items():
        selection = {
            "request_type": ChangeRequest.RequestType.PRODUCT,
            "target": product,
            "field_name": field_name,
            "label": label,
        }
        options.append(
            {
                "key": f"product:{field_name}",
                "label": label,
                "current": display_snapshot(snapshot_for_selection(selection)),
                "group": "产品信息",
            }
        )

    specs = (
        product.specs.filter(definition__active=True)
        .select_related("definition")
        .order_by("definition__display_order", "definition__display_name")
    )
    grouped_specs = {}
    for spec in specs:
        group = spec.definition.group or "其他规格"
        grouped_specs.setdefault(group, []).append(spec)
    for group, group_specs in grouped_specs.items():
        for spec in group_specs:
            options.append(
                {
                    "key": f"spec:{spec.pk}",
                    "label": spec.definition.display_name,
                    "current": spec.display_value,
                    "group": group,
                }
            )

    matches = (
        ProductMatch.objects.filter(
            Q(our_product=product) | Q(competitor_product=product),
            competitor_product__is_published=True,
        )
        .exclude(status=ProductMatch.Status.REJECTED)
        .select_related(
            "our_product__brand",
            "competitor_product__brand",
        )
        .distinct()
    )
    for match in matches:
        if match.our_product_id == product.pk:
            related_product = match.competitor_product
            relationship_label = "竞品"
        else:
            related_product = match.our_product
            relationship_label = "对标产品"
        related_name = f"{related_product.brand.name} {related_product.model}"
        group_label = f"对标关系 · {relationship_label} {related_name}"
        for field_name, label in MATCH_FIELDS.items():
            selection = {
                "request_type": ChangeRequest.RequestType.MATCH,
                "target": match,
                "field_name": field_name,
            }
            options.append(
                {
                    "key": f"match:{match.pk}:{field_name}",
                    "label": f"{related_name} · {label}",
                    "current": display_snapshot(
                        snapshot_for_selection(selection)
                    ),
                    "group": group_label,
                }
            )
        options.append(
            {
                "key": f"match:{match.pk}:{MATCH_DELETE_FIELD}",
                "label": f"删除对标关系 · {related_name}",
                "current": "当前有效",
                "group": group_label,
            }
        )
    return options


def resolve_target(product, target_key):
    parts = (target_key or "").split(":")
    product_fields = editable_product_fields(product)
    if len(parts) == 2 and parts[0] == "product" and parts[1] in product_fields:
        return {
            "request_type": ChangeRequest.RequestType.PRODUCT,
            "target": product,
            "field_name": parts[1],
            "label": product_fields[parts[1]],
        }
    if len(parts) == 2 and parts[0] == "spec" and parts[1].isdigit():
        spec = ProductSpec.objects.select_related("definition", "product").filter(
            pk=int(parts[1]),
            product=product,
            definition__active=True,
        ).first()
        if spec:
            return {
                "request_type": ChangeRequest.RequestType.SPEC,
                "target": spec,
                "field_name": spec.definition.code,
                "label": spec.definition.display_name,
            }
    if (
        len(parts) == 3
        and parts[0] == "match"
        and parts[1].isdigit()
        and parts[2] in {*MATCH_FIELDS, MATCH_DELETE_FIELD}
    ):
        match = (
            ProductMatch.objects.select_related(
                "our_product__brand",
                "competitor_product__brand",
            )
            .filter(
                pk=int(parts[1]),
                competitor_product__is_published=True,
            )
            .filter(Q(our_product=product) | Q(competitor_product=product))
            .exclude(status=ProductMatch.Status.REJECTED)
            .first()
        )
        if match:
            related_product = (
                match.competitor_product
                if match.our_product_id == product.pk
                else match.our_product
            )
            related_name = f"{related_product.brand.name} {related_product.model}"
            label = (
                f"删除对标关系 · {related_name}"
                if parts[2] == MATCH_DELETE_FIELD
                else f"{related_name} · {MATCH_FIELDS[parts[2]]}"
            )
            return {
                "request_type": ChangeRequest.RequestType.MATCH,
                "target": match,
                "field_name": parts[2],
                "label": label,
                "operation": (
                    "delete_match"
                    if parts[2] == MATCH_DELETE_FIELD
                    else "update"
                ),
            }
    raise ValidationError("所选修改字段无效或不属于当前产品。")


def parse_proposed_value(selection, raw_value):
    value = raw_value.strip()
    target = selection["target"]
    field_name = selection["field_name"]
    request_type = selection["request_type"]

    if (
        request_type == ChangeRequest.RequestType.MATCH
        and field_name == MATCH_DELETE_FIELD
    ):
        return {"delete": True}

    if request_type == ChangeRequest.RequestType.SPEC:
        data_type = target.definition.data_type
        if data_type in {"integer", "decimal"}:
            if not value:
                return {"value_text": "", "value_number": None}
            try:
                number = Decimal(value)
            except InvalidOperation as exc:
                raise ValidationError("建议值必须是有效数字。") from exc
            if data_type == "integer" and number != number.to_integral_value():
                raise ValidationError("该字段只接受整数。")
            return {"value_text": "", "value_number": _number_string(number)}
        if data_type == "boolean":
            normalized = value.lower()
            if normalized not in {"yes", "no", "true", "false", "1", "0"}:
                raise ValidationError("布尔字段请输入 Yes 或 No。")
            return {"value_boolean": normalized in {"yes", "true", "1"}}
        return {"value_text": value, "value_number": None}

    if request_type == ChangeRequest.RequestType.PRODUCT:
        if field_name in {"region", "wifi_standard"} and not value:
            raise ValidationError("该产品字段不能为空。")
        if field_name == "ap_type" and value not in Product.APType.values:
            raise ValidationError("AP Type 建议值无效。")
        if field_name == "lifecycle_status" and value not in Product.LifecycleStatus.values:
            raise ValidationError("Lifecycle Status 建议值无效。")
        if field_name in {"official_url", "datasheet_url"} and value:
            URLValidator()(value)
        if field_name == "launch_date" and value:
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ValidationError(
                    "Launch Date must use YYYY-MM-DD format."
                ) from exc
        return {"value": value}

    if field_name == "match_type" and value not in ProductMatch.MatchType.values:
        raise ValidationError("Match Type 建议值无效。")
    if field_name == "match_level" and value not in ProductMatch.MatchLevel.values:
        raise ValidationError("Match Level 建议值无效。")
    if field_name == "status" and value not in ProductMatch.Status.values:
        raise ValidationError("Status 建议值无效。")
    if field_name in {"match_score", "confidence"}:
        if not value:
            return {"value": None}
        try:
            score = int(value)
        except ValueError as exc:
            raise ValidationError("该字段必须是 0–100 的整数。") from exc
        if not 0 <= score <= 100:
            raise ValidationError("该字段必须是 0–100 的整数。")
        return {"value": score}
    if field_name == "rank":
        try:
            rank = int(value)
        except ValueError as exc:
            raise ValidationError("Rank 必须是非负整数。") from exc
        if rank < 0:
            raise ValidationError("Rank 必须是非负整数。")
        return {"value": rank}
    if field_name in {"valid_from", "valid_to"} and value:
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValidationError("日期必须使用 YYYY-MM-DD 格式。") from exc
    if field_name == "source_url" and value:
        URLValidator()(value)
    return {"value": value}


def proposed_value_hint(selection):
    target = selection["target"]
    field_name = selection["field_name"]
    if field_name == MATCH_DELETE_FIELD:
        return "该申请获批后，对标关系会标记为已删除并立即停止展示。"
    if selection["request_type"] == ChangeRequest.RequestType.SPEC:
        if target.definition.data_type == "integer":
            return f"请输入整数{f'，单位 {target.definition.unit}' if target.definition.unit else ''}。"
        if target.definition.data_type == "decimal":
            return f"请输入数字{f'，单位 {target.definition.unit}' if target.definition.unit else ''}。"
        if target.definition.data_type == "boolean":
            return "请输入 Yes 或 No。"
    if field_name == "ap_type":
        return "可用值：" + "、".join(value for value, _ in Product.APType.choices)
    if field_name == "lifecycle_status":
        return "可用值：" + "、".join(value for value, _ in Product.LifecycleStatus.choices)
    if field_name == "match_type":
        return "可用值：" + "、".join(value for value, _ in ProductMatch.MatchType.choices)
    if field_name == "match_level":
        return "可用值：" + "、".join(value for value, _ in ProductMatch.MatchLevel.choices)
    if field_name == "status":
        return "可用值：" + "、".join(value for value, _ in ProductMatch.Status.choices)
    if field_name == "launch_date":
        return "请使用 YYYY-MM-DD 格式；留空可清除日期。"
    if field_name in {"match_score", "confidence"}:
        return "请输入 0–100 的整数，留空表示 Unknown。"
    if field_name == "rank":
        return "请输入非负整数。"
    if field_name in {"valid_from", "valid_to"}:
        return "请使用 YYYY-MM-DD 格式；留空可清除日期。"
    return "输入该字段的完整建议值；允许留空以清除可选字段。"


def current_snapshot(change, target):
    if (
        change.request_type == ChangeRequest.RequestType.MATCH
        and change.field_name == MATCH_ADD_FIELD
    ):
        return {"exists": _active_match_exists(change)}
    selection = {
        "request_type": change.request_type,
        "target": target,
        "field_name": change.field_name,
    }
    return snapshot_for_selection(selection)


def _locked_target(change):
    if change.request_type == ChangeRequest.RequestType.SPEC:
        return ProductSpec.objects.select_for_update().select_related("definition", "product").get(pk=change.target_spec_id)
    if change.request_type == ChangeRequest.RequestType.MATCH:
        return ProductMatch.objects.select_for_update().get(pk=change.target_match_id)
    return Product.objects.select_for_update().get(pk=change.target_product_id)


def _apply_proposed(change, target, reviewer):
    proposed = change.proposed_value
    if change.request_type == ChangeRequest.RequestType.SPEC:
        target.value_status = ProductSpec.ValueStatus.PUBLISHED
        target.value_text = proposed.get("value_text", "")
        number = proposed.get("value_number")
        target.value_number = Decimal(number) if number is not None else None
        target.value_boolean = proposed.get("value_boolean")
        if change.source_url:
            target.source_url = change.source_url
        target.updated_by = reviewer
    elif (
        change.request_type == ChangeRequest.RequestType.MATCH
        and change.field_name == MATCH_DELETE_FIELD
    ):
        target.status = ProductMatch.Status.REJECTED
        target.updated_by = reviewer
    else:
        setattr(target, change.field_name, proposed["value"])
        target.updated_by = reviewer
    target.save()


def _active_match_exists(change):
    proposed = change.proposed_value
    queryset = ProductMatch.objects.filter(
        our_product_id=change.target_product_id,
        competitor_product_id=proposed["competitor_product_id"],
    ).exclude(status=ProductMatch.Status.REJECTED)
    benchmark_case_id = proposed.get("benchmark_case_id")
    if benchmark_case_id:
        queryset = queryset.filter(benchmark_case_id=benchmark_case_id)
    else:
        queryset = queryset.filter(
            benchmark_case_id=None,
            region=proposed["region"],
        )
    return queryset.exists()


def _apply_match_add(change, reviewer):
    proposed = change.proposed_value
    benchmark_case_id = proposed.get("benchmark_case_id")
    lookup = {
        "our_product_id": change.target_product_id,
        "competitor_product_id": proposed["competitor_product_id"],
    }
    if benchmark_case_id:
        lookup["benchmark_case_id"] = benchmark_case_id
    else:
        lookup["benchmark_case_id"] = None
        lookup["region"] = proposed["region"]

    match = ProductMatch.objects.filter(**lookup).first()
    if match is None:
        match = ProductMatch(**lookup, created_by=reviewer)
    rank = proposed.get("rank")
    if rank is None:
        rank = (
            ProductMatch.objects.filter(
                our_product_id=change.target_product_id,
                benchmark_case_id=benchmark_case_id,
            ).aggregate(max_rank=Max("rank"))["max_rank"]
            or 0
        ) + 1
    match.region = proposed["region"]
    match.match_type = proposed["match_type"]
    match.match_level = proposed["match_level"]
    match.status = ProductMatch.Status.CONFIRMED
    match.rank = rank
    match.match_score = proposed.get("match_score")
    match.confidence = proposed.get("confidence")
    match.reason = proposed.get("reason", "")
    match.source_url = proposed.get("source_url", "")
    match.updated_by = reviewer
    match.save()
    return match


@transaction.atomic
def approve_change(change_id, reviewer, review_comment, ip):
    change = ChangeRequest.objects.select_for_update().select_related(
        "target_product", "target_spec", "target_match", "submitted_by"
    ).get(pk=change_id)
    if change.status != ChangeRequest.Status.PENDING:
        raise ValidationError("该申请已经完成审核。")
    if (
        change.request_type == ChangeRequest.RequestType.MATCH
        and change.field_name == MATCH_ADD_FIELD
    ):
        Product.objects.select_for_update().get(pk=change.target_product_id)
        before = {"exists": _active_match_exists(change)}
        if before != change.old_value:
            raise ApprovalConflict(
                "该竞品对标关系已在申请提交后发生变化，请重新提交申请。"
            )
        match = _apply_match_add(change, reviewer)
        after = {
            "exists": True,
            "match_id": match.pk,
            "competitor_product_id": match.competitor_product_id,
        }
        change.status = ChangeRequest.Status.APPROVED
        change.reviewed_by = reviewer
        change.reviewed_at = timezone.now()
        change.review_comment = review_comment.strip()
        change.save()
        AuditLog.objects.create(
            actor=reviewer,
            action="change_request.approved",
            object_type=match._meta.label,
            object_id=str(match.pk),
            object_repr=str(match),
            before_data=before,
            after_data=after,
            ip_address=ip,
        )
        return change
    target = _locked_target(change)
    before = current_snapshot(change, target)
    if before != change.old_value:
        raise ApprovalConflict("当前正式值已在申请提交后发生变化，请重新提交申请。")
    _apply_proposed(change, target, reviewer)
    after = current_snapshot(change, target)
    change.status = ChangeRequest.Status.APPROVED
    change.reviewed_by = reviewer
    change.reviewed_at = timezone.now()
    change.review_comment = review_comment.strip()
    change.save()
    AuditLog.objects.create(
        actor=reviewer,
        action="change_request.approved",
        object_type=target._meta.label,
        object_id=str(target.pk),
        object_repr=str(target),
        before_data=before,
        after_data=after,
        ip_address=ip,
    )
    return change


@transaction.atomic
def reject_change(change_id, reviewer, review_comment, ip):
    comment = review_comment.strip()
    if not comment:
        raise ValidationError("拒绝申请时必须填写审核意见。")
    change = ChangeRequest.objects.select_for_update().get(pk=change_id)
    if change.status != ChangeRequest.Status.PENDING:
        raise ValidationError("该申请已经完成审核。")
    change.status = ChangeRequest.Status.REJECTED
    change.reviewed_by = reviewer
    change.reviewed_at = timezone.now()
    change.review_comment = comment
    change.save()
    AuditLog.objects.create(
        actor=reviewer,
        action="change_request.rejected",
        object_type=change._meta.label,
        object_id=str(change.pk),
        object_repr=str(change),
        before_data={"status": ChangeRequest.Status.PENDING},
        after_data={"status": ChangeRequest.Status.REJECTED, "comment": comment},
        ip_address=ip,
    )
    return change
