from flyalpha.runner import build_parser


def test_runner_accepts_stats_command():
    args = build_parser().parse_args(["stats", "--episodes", "3"])

    assert args.command == "stats"
    assert args.episodes == 3


def test_runner_accepts_tune_command():
    args = build_parser().parse_args(["tune", "--episodes", "3", "--limit", "2"])

    assert args.command == "tune"
    assert args.episodes == 3
    assert args.limit == 2


def test_runner_accepts_csv_stats_command():
    args = build_parser().parse_args(["stats", "--csv", "data.csv", "--limit", "100", "--save-report"])

    assert args.command == "stats"
    assert args.csv == "data.csv"
    assert args.limit == 100
    assert args.save_report is True


def test_runner_accepts_validate_command():
    args = build_parser().parse_args(["validate", "--csv", "data.csv", "--train-fraction", "0.6"])

    assert args.command == "validate"
    assert args.csv == "data.csv"
    assert args.train_fraction == 0.6


def test_runner_accepts_pf_tuning_controls():
    args = build_parser().parse_args(
        [
            "tune",
            "--objective",
            "profit_factor",
            "--no-progress",
            "--save-report",
            "--confidence-thresholds",
            "0,0.1",
            "--trend-alignments",
            "false,true",
            "--breakeven-trigger-pcts",
            "none,0.005",
        ]
    )

    assert args.objective == "profit_factor"
    assert args.no_progress is True
    assert args.save_report is True
    assert args.confidence_thresholds == "0,0.1"


def test_runner_accepts_new_experiment_commands():
    walk = build_parser().parse_args(
        ["walk-forward", "--csv", "data.csv", "--train-size", "10", "--test-size", "5", "--step-size", "5"]
    )
    ablate = build_parser().parse_args(["ablate", "--csv", "data.csv", "--controls", "full,random_reward"])
    credit = build_parser().parse_args(["credit", "--csv", "data.csv", "--reward-delays", "0,3"])

    assert walk.command == "walk-forward"
    assert ablate.controls == "full,random_reward"
    assert credit.reward_delays == "0,3"
