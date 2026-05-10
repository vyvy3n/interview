"""
Level 3 tests — Context Window + Truncation
Run: python3 test_level3.py
"""

import unittest
from solution import ConversationService


class TestLevel3SetContextLimit(unittest.TestCase):

    def test_set_limit_no_drops_needed(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 10)
        dropped = s.set_context_limit("c1", 50)
        self.assertEqual(dropped, 0)

    def test_set_limit_drops_oldest(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "First", 10)
        s.add_message("c1", "assistant", "Second", 10)
        s.add_message("c1", "user", "Third", 10)  # total = 30
        dropped = s.set_context_limit("c1", 20)
        self.assertEqual(dropped, 1)
        # Oldest ("First") dropped; 2 remain
        self.assertEqual(s.get_message_count("c1"), 2)
        msgs = s.get_messages("c1")
        self.assertNotIn("user:First", msgs)

    def test_set_limit_drops_multiple(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "A", 10)
        s.add_message("c1", "assistant", "B", 10)
        s.add_message("c1", "user", "C", 10)
        s.add_message("c1", "assistant", "D", 10)  # total = 40
        dropped = s.set_context_limit("c1", 15)
        # Need to drop until <=15: drop A(30), B(20), C(10) -> 10<=15
        self.assertEqual(dropped, 3)
        self.assertEqual(s.get_message_count("c1"), 1)

    def test_set_limit_missing_conv(self):
        s = ConversationService()
        self.assertEqual(s.set_context_limit("ghost", 100), -1)

    def test_set_limit_exact_total(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 20)
        dropped = s.set_context_limit("c1", 20)
        self.assertEqual(dropped, 0)
        self.assertEqual(s.get_message_count("c1"), 1)


class TestLevel3AddMessageWithBudget(unittest.TestCase):

    def test_no_limit_returns_zero_drops(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        result = s.add_message_with_budget("c1", "user", "Hello", 10)
        self.assertEqual(result, 0)
        self.assertEqual(s.get_message_count("c1"), 1)

    def test_with_limit_no_drops_needed(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.set_context_limit("c1", 50)
        result = s.add_message_with_budget("c1", "user", "Hello", 10)
        self.assertEqual(result, 0)

    def test_with_limit_drops_oldest(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Old", 20)
        s.set_context_limit("c1", 30)
        # Current = 20; adding 15 -> 35 > 30; drop "Old" (20) -> 0 + 15 = 15 <= 30
        drops = s.add_message_with_budget("c1", "user", "New", 15)
        self.assertEqual(drops, 1)
        msgs = s.get_messages("c1")
        self.assertEqual(msgs, ["user:New"])

    def test_reject_single_message_exceeds_limit(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.set_context_limit("c1", 10)
        result = s.add_message_with_budget("c1", "user", "Too big", 20)
        self.assertEqual(result, -1)
        self.assertEqual(s.get_message_count("c1"), 0)  # no state change

    def test_reject_does_not_modify_state(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Keep me", 8)
        s.set_context_limit("c1", 10)
        # Reject: 15 > 10
        s.add_message_with_budget("c1", "user", "Giant", 15)
        # Original message still there
        self.assertEqual(s.get_message_count("c1"), 1)
        self.assertEqual(s.get_messages("c1"), ["user:Keep me"])

    def test_missing_conv_returns_neg_one(self):
        s = ConversationService()
        self.assertEqual(s.add_message_with_budget("ghost", "user", "Hi", 5), -1)

    def test_drops_multiple_to_fit(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "A", 10)
        s.add_message("c1", "assistant", "B", 10)
        s.add_message("c1", "user", "C", 10)
        s.set_context_limit("c1", 30)
        # Total=30; adding 15 -> 45 > 30; drop A(20), still 35>30; drop B(10), 25<=30
        drops = s.add_message_with_budget("c1", "user", "New", 15)
        self.assertEqual(drops, 2)
        self.assertEqual(s.get_message_count("c1"), 2)

    def test_l1_add_message_ignores_limit(self):
        """L1 add_message does NOT enforce the context limit."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.set_context_limit("c1", 5)
        # L1 add_message ignores limit — just appends
        total = s.add_message("c1", "user", "Way too big", 100)
        self.assertEqual(total, 100)  # returned cumulative, not -1
        self.assertEqual(s.get_message_count("c1"), 1)

    def test_add_with_budget_exact_fit(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.set_context_limit("c1", 20)
        s.add_message("c1", "user", "A", 10)
        drops = s.add_message_with_budget("c1", "user", "B", 10)
        self.assertEqual(drops, 0)  # 10 + 10 = 20 == limit, fits perfectly
        self.assertEqual(s.get_message_count("c1"), 2)


class TestLevel3SummarizeToBudget(unittest.TestCase):

    def test_summarize_basic(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "A", 10)
        s.add_message("c1", "assistant", "B", 10)
        s.add_message("c1", "user", "C", 10)  # total = 30
        kept = s.summarize_to_budget("c1", 15)
        # Drop A(20), B(10), 10<=15 -> keep [C]
        self.assertEqual(kept, 1)

    def test_summarize_already_within_budget(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 5)
        kept = s.summarize_to_budget("c1", 100)
        self.assertEqual(kept, 1)

    def test_summarize_missing_conv(self):
        s = ConversationService()
        self.assertEqual(s.summarize_to_budget("ghost", 100), -1)

    def test_summarize_drops_all(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "A", 10)
        s.add_message("c1", "assistant", "B", 10)
        # Budget = 5, but each msg has 10 tokens. Drop all.
        kept = s.summarize_to_budget("c1", 5)
        self.assertEqual(kept, 0)
        self.assertEqual(s.get_message_count("c1"), 0)

    def test_summarize_does_not_set_limit(self):
        """summarize_to_budget is a one-shot trim; doesn't set persistent limit."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "A", 10)
        s.summarize_to_budget("c1", 5)
        # Now add a big message using L1 add_message — should work (no limit set)
        total = s.add_message("c1", "user", "Big", 100)
        self.assertEqual(total, 100)  # no limit, appended fine

    def test_summarize_returns_correct_kept_count(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        for i in range(10):
            s.add_message("c1", "user", f"msg{i}", 5)  # 10 msgs, 50 tokens
        kept = s.summarize_to_budget("c1", 25)
        self.assertEqual(kept, 5)


if __name__ == "__main__":
    unittest.main()
