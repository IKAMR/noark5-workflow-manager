import unittest

from noark5_workflow.core.workflow import Workflow


class WorkflowModelTests(unittest.TestCase):
    def test_add_remove_clear_and_order(self):
        workflow = Workflow()
        self.assertTrue(workflow.add("a"))
        self.assertTrue(workflow.add("b"))
        self.assertFalse(workflow.add("a"))
        self.assertEqual(workflow.operation_ids(), ["a", "b"])
        self.assertTrue(workflow.remove("a"))
        self.assertEqual(workflow.operation_ids(), ["b"])
        workflow.clear()
        self.assertEqual(workflow.operation_ids(), [])


if __name__ == "__main__":
    unittest.main()
