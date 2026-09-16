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
    args = build_parser().parse_args(["stats", "--csv", "data.csv", "--limit", "100"])

    assert args.command == "stats"
    assert args.csv == "data.csv"
    assert args.limit == 100
