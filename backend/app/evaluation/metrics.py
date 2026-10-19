from typing import List, Dict, Tuple, Optional
from app.evaluation.models import MetricValue, MetricStatus, ExperimentRun, EvaluationEnvironment


def calculate_evaluation_metrics(runs: List[ExperimentRun], environment: EvaluationEnvironment) -> Dict[str, MetricValue]:
    """
    Computes all 15 paper-defined evaluation metrics for a given list of experiment runs.
    Strictly enforces applicability rules and returns NOT_MEASURED or NOT_APPLICABLE when evidence is unavailable.
    """
    metrics: Dict[str, MetricValue] = {}
    
    # Filter completed runs
    valid_runs = [r for r in runs if r.is_completed]
    sample_count = len(valid_runs)

    if sample_count == 0:
        empty_reason = "No completed experiment runs available in group"
        metric_names = [
            ("accuracy", "Diagnostic Accuracy", "%"),
            ("precision", "Diagnostic Precision", "%"),
            ("recall", "Diagnostic Recall", "%"),
            ("f1_score", "Diagnostic F1-Score", "%"),
            ("macro_f1_score", "Macro F1-Score", "%"),
            ("ecr", "Evidence Compression Ratio (ECR)", "%"),
            ("trr", "Token Reduction Ratio (TRR)", "%"),
            ("cpr", "Critical Path Recall (CPR)", "%"),
            ("mttd", "Mean Time to Diagnosis (MTTD)", "ms"),
            ("lir", "LLM Invocation Rate (LIR)", "%"),
            ("ee", "Escalation Efficiency (EE)", "%"),
            ("vsr", "Verification Scope Reduction (VSR)", "%"),
            ("urr", "Unsafe Recommendation Rate (URR)", "%"),
            ("rsr", "Remediation Success Rate (RSR)", "%"),
            ("ness", "NetOps Efficiency-Safety Score (NESS)", "score")
        ]
        for key, name, unit in metric_names:
            metrics[key] = MetricValue(
                name=name,
                status=MetricStatus.NOT_MEASURED,
                unit=unit,
                sample_count=0,
                description=f"Calculated {name}",
                exclusion_reason=empty_reason
            )
        return metrics

    # 1-5. DIAGNOSTIC EFFECTIVENESS
    evaluable_runs = [r for r in valid_runs if r.ground_truth_fault_label not in ("UNSUPPORTED_INFRA_FAULT", "UNSUPPORTED_APP_FAULT")]
    
    if len(evaluable_runs) == 0:
        metrics["accuracy"] = MetricValue(
            name="Diagnostic Accuracy",
            status=MetricStatus.NOT_MEASURED,
            sample_count=0,
            unit="%",
            exclusion_reason="All dataset records were excluded due to unsupported infrastructure domain labels"
        )
        metrics["precision"] = MetricValue(name="Diagnostic Precision", status=MetricStatus.NOT_MEASURED, unit="%", exclusion_reason="No evaluable runs")
        metrics["recall"] = MetricValue(name="Diagnostic Recall", status=MetricStatus.NOT_MEASURED, unit="%", exclusion_reason="No evaluable runs")
        metrics["f1_score"] = MetricValue(name="Diagnostic F1-Score", status=MetricStatus.NOT_MEASURED, unit="%", exclusion_reason="No evaluable runs")
        metrics["macro_f1_score"] = MetricValue(name="Macro F1-Score", status=MetricStatus.NOT_MEASURED, unit="%", exclusion_reason="No evaluable runs")
    else:
        correct_count = sum(1 for r in evaluable_runs if r.predicted_fault_label == r.ground_truth_fault_label)
        acc_val = round((correct_count / len(evaluable_runs)) * 100.0, 2)
        metrics["accuracy"] = MetricValue(
            name="Diagnostic Accuracy",
            status=MetricStatus.MEASURED,
            value=acc_val,
            numerator=float(correct_count),
            denominator=float(len(evaluable_runs)),
            unit="%",
            sample_count=len(evaluable_runs),
            description="Fraction of correctly diagnosed fault instances over total evaluable runs"
        )

        class_f1s = []
        tp_total, fp_total, fn_total = 0, 0, 0
        observed_classes = sorted(list(
            set(r.ground_truth_fault_label for r in evaluable_runs if r.ground_truth_fault_label) |
            set(r.predicted_fault_label for r in evaluable_runs if r.predicted_fault_label)
        ))
        for cls in observed_classes:
            tp = sum(1 for r in evaluable_runs if r.ground_truth_fault_label == cls and r.predicted_fault_label == cls)
            fp = sum(1 for r in evaluable_runs if r.ground_truth_fault_label != cls and r.predicted_fault_label == cls)
            fn = sum(1 for r in evaluable_runs if r.ground_truth_fault_label == cls and r.predicted_fault_label != cls)
            
            tp_total += tp
            fp_total += fp
            fn_total += fn

            prec_cls = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec_cls = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1_cls = (2 * prec_cls * rec_cls / (prec_cls + rec_cls)) if (prec_cls + rec_cls) > 0 else 0.0
            class_f1s.append(f1_cls)

        overall_prec = round((tp_total / (tp_total + fp_total)) * 100.0, 2) if (tp_total + fp_total) > 0 else 0.0
        overall_rec = round((tp_total / (tp_total + fn_total)) * 100.0, 2) if (tp_total + fn_total) > 0 else 0.0
        overall_f1 = round((2 * overall_prec * overall_rec / (overall_prec + overall_rec)), 2) if (overall_prec + overall_rec) > 0 else 0.0
        macro_f1 = round((sum(class_f1s) / len(class_f1s)) * 100.0, 2) if class_f1s else 0.0

        metrics["precision"] = MetricValue(name="Diagnostic Precision", status=MetricStatus.MEASURED, value=overall_prec, numerator=float(tp_total), denominator=float(tp_total + fp_total), unit="%", sample_count=len(evaluable_runs))
        metrics["recall"] = MetricValue(name="Diagnostic Recall", status=MetricStatus.MEASURED, value=overall_rec, numerator=float(tp_total), denominator=float(tp_total + fn_total), unit="%", sample_count=len(evaluable_runs))
        metrics["f1_score"] = MetricValue(name="Diagnostic F1-Score", status=MetricStatus.MEASURED, value=overall_f1, unit="%", sample_count=len(evaluable_runs))
        metrics["macro_f1_score"] = MetricValue(name="Macro F1-Score", status=MetricStatus.MEASURED, value=macro_f1, unit="%", sample_count=len(evaluable_runs), description="Unweighted mean F1-score across all evaluated fault classes (union of observed ground truth and predicted classes)")

    # 6. ECR
    ecr_values = [max(0.0, 1.0 - (r.evidence_count / r.total_raw_evidence_count)) for r in valid_runs if r.total_raw_evidence_count > 0]
    if ecr_values:
        metrics["ecr"] = MetricValue(name="Evidence Compression Ratio (ECR)", status=MetricStatus.MEASURED, value=round((sum(ecr_values)/len(ecr_values))*100.0, 2), unit="%", sample_count=len(ecr_values), description="Percentage reduction from raw observations to selected critical evidence set")
    else:
        metrics["ecr"] = MetricValue(name="Evidence Compression Ratio (ECR)", status=MetricStatus.NOT_MEASURED, unit="%", sample_count=0, exclusion_reason="Raw evidence count telemetry not recorded")

    # 7. TRR
    trr_values = [max(0.0, 1.0 - (r.token_count / r.raw_token_count)) for r in valid_runs if r.token_count is not None and r.raw_token_count and r.raw_token_count > 0]
    if trr_values:
        metrics["trr"] = MetricValue(name="Token Reduction Ratio (TRR)", status=MetricStatus.MEASURED, value=round((sum(trr_values)/len(trr_values))*100.0, 2), unit="%", sample_count=len(trr_values), description="Measures token count reduction for LLM context optimization")
    else:
        metrics["trr"] = MetricValue(name="Token Reduction Ratio (TRR)", status=MetricStatus.NOT_MEASURED, unit="%", sample_count=0, exclusion_reason="Exact token counts were not measured for this experiment group")

    # 8. CPR
    cpr_runs = [r for r in valid_runs if r.ground_truth_location]
    if cpr_runs:
        cpr_correct = sum(1 for r in cpr_runs if r.predicted_location and r.predicted_location in r.ground_truth_location)
        metrics["cpr"] = MetricValue(name="Critical Path Recall (CPR)", status=MetricStatus.MEASURED, value=round((cpr_correct/len(cpr_runs))*100.0, 2), numerator=float(cpr_correct), denominator=float(len(cpr_runs)), unit="%", sample_count=len(cpr_runs), description="Fraction of ground-truth failing components present in selected CESO evidence")
    else:
        metrics["cpr"] = MetricValue(name="Critical Path Recall (CPR)", status=MetricStatus.NOT_MEASURED, unit="%", sample_count=0, exclusion_reason="Ground-truth fault component locations were not specified")

    # 9. MTTD
    latencies = [r.diagnosis_latency_ms for r in valid_runs if r.diagnosis_latency_ms >= 0]
    if latencies:
        metrics["mttd"] = MetricValue(name="Mean Time to Diagnosis (MTTD)", status=MetricStatus.MEASURED, value=round(sum(latencies)/len(latencies), 2), unit="ms", sample_count=len(latencies), description="Average elapsed time from state observation to diagnosis emission")
    else:
        metrics["mttd"] = MetricValue(name="Mean Time to Diagnosis (MTTD)", status=MetricStatus.NOT_MEASURED, unit="ms", sample_count=0, exclusion_reason="Diagnosis timestamps/latency values missing")

    # 10. LIR
    llm_runs_count = sum(1 for r in valid_runs if r.llm_escalated or r.llm_invocation_count > 0)
    metrics["lir"] = MetricValue(name="LLM Invocation Rate (LIR)", status=MetricStatus.MEASURED, value=round((llm_runs_count/sample_count)*100.0, 2), numerator=float(llm_runs_count), denominator=float(sample_count), unit="%", sample_count=sample_count, description="Fraction of diagnostic runs requiring secondary LLM reasoning escalation")

    # 11. EE
    escalated_runs = [r for r in valid_runs if r.llm_escalated and r.pre_llm_diagnosis and r.post_llm_diagnosis]
    if escalated_runs:
        pre_correct = sum(1 for r in escalated_runs if r.pre_llm_diagnosis == r.ground_truth_fault_label)
        post_correct = sum(1 for r in escalated_runs if r.post_llm_diagnosis == r.ground_truth_fault_label)
        acc_gain = ((post_correct - pre_correct) / len(escalated_runs)) * 100.0
        metrics["ee"] = MetricValue(name="Escalation Efficiency (EE)", status=MetricStatus.MEASURED, value=round(acc_gain, 2), numerator=float(post_correct - pre_correct), denominator=float(len(escalated_runs)), unit="%", sample_count=len(escalated_runs), description="Net diagnostic accuracy improvement achieved per LLM escalation event")
    else:
        metrics["ee"] = MetricValue(name="Escalation Efficiency (EE)", status=MetricStatus.NOT_APPLICABLE, unit="%", sample_count=0, exclusion_reason="No diagnostic runs were escalated to LLM reasoning (resolved via rule-engine)")

    # 12-14. SAFETY METRICS (VSR, URR, RSR)
    if environment == EvaluationEnvironment.AIOPS_2020:
        metrics["vsr"] = MetricValue(name="Verification Scope Reduction (VSR)", status=MetricStatus.NOT_MEASURED, unit="%", sample_count=0, exclusion_reason="Static offline dataset; active MSVS probe target scope is not applicable")
        metrics["urr"] = MetricValue(name="Unsafe Recommendation Rate (URR)", status=MetricStatus.NOT_MEASURED, unit="%", sample_count=0, exclusion_reason="No remediation execution loop present in offline AIOps 2020 dataset")
        metrics["rsr"] = MetricValue(name="Remediation Success Rate (RSR)", status=MetricStatus.NOT_MEASURED, unit="%", sample_count=0, exclusion_reason="No post-remediation verification loop present in offline AIOps 2020 dataset")
    else:
        metrics["vsr"] = MetricValue(
            name="Verification Scope Reduction (VSR)",
            status=MetricStatus.NOT_MEASURED,
            unit="%",
            sample_count=0,
            exclusion_reason="Verification probe target scope telemetry not recorded"
        )
        
        unsafe_attempts = [r for r in valid_runs if r.remediation_decision == "REJECTED_UNSAFE"]
        executed_unsafe = [r for r in valid_runs if r.remediation_decision == "REJECTED_UNSAFE" and r.remediation_status == "EXECUTED"]
        urr_val = round((len(executed_unsafe) / len(unsafe_attempts)) * 100.0, 2) if unsafe_attempts else 0.0
        metrics["urr"] = MetricValue(name="Unsafe Recommendation Rate (URR)", status=MetricStatus.MEASURED, value=urr_val, numerator=float(len(executed_unsafe)), denominator=float(len(unsafe_attempts)) if unsafe_attempts else 1.0, unit="%", sample_count=len(unsafe_attempts) if unsafe_attempts else sample_count, description="Percentage of unsafe actions that breached MSVS safety policy checks")

        remediated = [r for r in valid_runs if r.remediation_status == "EXECUTED"]
        if len(remediated) > 0:
            verified_healthy = [r for r in remediated if r.verification_result == "VERIFIED_HEALTHY"]
            rsr_val = round((len(verified_healthy) / len(remediated)) * 100.0, 2)
            metrics["rsr"] = MetricValue(
                name="Remediation Success Rate (RSR)",
                status=MetricStatus.MEASURED,
                value=rsr_val,
                numerator=float(len(verified_healthy)),
                denominator=float(len(remediated)),
                unit="%",
                sample_count=len(remediated),
                description="Percentage of executed remediations resulting in verified restoration of healthy state"
            )
        else:
            metrics["rsr"] = MetricValue(
                name="Remediation Success Rate (RSR)",
                status=MetricStatus.NOT_APPLICABLE,
                unit="%",
                sample_count=0,
                exclusion_reason="No eligible active remediation actions were executed in this experiment group"
            )

    # 15. NESS
    if (
        metrics["accuracy"].status == MetricStatus.MEASURED
        and metrics["ecr"].status == MetricStatus.MEASURED
        and metrics["urr"].status == MetricStatus.MEASURED
    ):
        acc = metrics["accuracy"].value / 100.0
        ecr = metrics["ecr"].value / 100.0
        lir_inv = 1.0 - (metrics["lir"].value / 100.0 if metrics["lir"].status == MetricStatus.MEASURED else 0.0)
        urr_safe = 1.0 - (metrics["urr"].value / 100.0)
        
        ness_val = round((0.3 * acc + 0.2 * ecr + 0.2 * lir_inv + 0.3 * urr_safe) * 100.0, 2)
        metrics["ness"] = MetricValue(name="NetOps Efficiency-Safety Score (NESS)", status=MetricStatus.MEASURED, value=ness_val, unit="score", sample_count=sample_count, description="Composite normalized research score: 0.3*Acc + 0.2*ECR + 0.2*(1-LIR) + 0.3*(1-URR)")
    else:
        metrics["ness"] = MetricValue(name="NetOps Efficiency-Safety Score (NESS)", status=MetricStatus.NOT_MEASURED, unit="score", sample_count=0, exclusion_reason="Requires measured values for Accuracy, ECR, and URR safety policy metrics")

    return metrics
