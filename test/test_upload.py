from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, call, mock_open, patch

from mofeapi.enums import AggregateType, Difficulty
from mofeapi.models.testcase import Testcase, TestcaseSet, TestcaseSetBase

from models import ProblemConfig, TestcaseSetWithRegex
from upload import upload_testcases


class TestUploadTestcases(TestCase):
    def test_new_partial_score_set_uses_created_set_id(self):
        problem_id = 9999
        sample_set = TestcaseSet(
            aggregate_type=AggregateType.ALL,
            name="sample",
            points=0,
            id=1,
            is_sample=True,
        )
        all_set = TestcaseSet(
            aggregate_type=AggregateType.ALL,
            name="all",
            points=100,
            id=2,
            is_sample=False,
        )
        partial_set = TestcaseSet(
            aggregate_type=AggregateType.ALL,
            name="partial",
            points=30,
            id=3,
            is_sample=False,
        )

        sample_case = Testcase(id=10, name="00_sample_01", testcase_sets=[])
        partial_case = Testcase(id=11, name="10_partial_01", testcase_sets=[])

        client = MagicMock()
        client.get_testcases.side_effect = [
            ([sample_set, all_set], []),
            ([sample_set, all_set], [sample_case, partial_case]),
            ([sample_set, all_set, partial_set], [sample_case, partial_case]),
        ]

        problem_config = ProblemConfig(
            problem_id=problem_id,
            difficulty=Difficulty.MILK,
            execution_time_limit=2000,
            submission_limit_1=5,
            submission_limit_2=60,
            position_in_contest="A",
            testcase_sets=[
                TestcaseSetWithRegex(
                    regex=r"00_sample_\d+",
                    testcase_set=TestcaseSetBase(
                        aggregate_type=AggregateType.ALL,
                        name="sample",
                        points=0,
                    ),
                ),
                TestcaseSetWithRegex(
                    regex=r"10_partial_\d+",
                    testcase_set=TestcaseSetBase(
                        aggregate_type=AggregateType.ALL,
                        name="partial",
                        points=30,
                    ),
                ),
                TestcaseSetWithRegex(
                    regex=r".",
                    testcase_set=TestcaseSetBase(
                        aggregate_type=AggregateType.ALL,
                        name="all",
                        points=100,
                    ),
                ),
            ],
        )

        with patch("builtins.open", mock_open(read_data=b"zip")):
            upload_testcases(client, problem_config, Path("testcases.zip"))

        client.create_testcase_set.assert_called_once()
        self.assertEqual(
            client.add_to_testcase_set_multiple.call_args_list,
            [
                call(problem_id, sample_set.id, [sample_case.id]),
                call(problem_id, partial_set.id, [partial_case.id]),
                call(problem_id, all_set.id, [sample_case.id, partial_case.id]),
            ],
        )
