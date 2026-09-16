from flyalpha.mushroom_body import DopamineSignal, KCToMBONPlasticity, KenyonActivity


def test_dopamine_changes_only_eligible_synapses():
    plasticity = KCToMBONPlasticity(learning_rate=0.5, trace_decay=1.0)
    activity = KenyonActivity(active_cells=frozenset({"kc_return_pos"}))

    plasticity.activate(activity, "approach")
    plasticity.apply_dopamine(DopamineSignal.from_prediction_error(1.0))

    assert plasticity.weights[("kc_return_pos", "approach")] == 0.5
    assert ("kc_return_pos", "avoidance") not in plasticity.weights

