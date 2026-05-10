"""
Level 4 tests — Fork, Branch, and Merge
Run: python3 test_level4.py
"""

import unittest
from solution import ConversationService


class TestLevel4ForkConversation(unittest.TestCase):

    def test_fork_basic(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "Hello", 10)
        self.assertTrue(s.fork_conversation("src", "fork1"))
        self.assertEqual(s.get_message_count("fork1"), 1)

    def test_fork_missing_source(self):
        s = ConversationService()
        self.assertFalse(s.fork_conversation("ghost", "new"))

    def test_fork_new_id_exists(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.create_conversation("fork1", "alice")
        self.assertFalse(s.fork_conversation("src", "fork1"))

    def test_fork_independence(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "Original", 10)
        s.fork_conversation("src", "fork1")
        # Modify fork — original unaffected
        s.add_message("fork1", "assistant", "Fork reply", 8)
        self.assertEqual(s.get_message_count("src"), 1)
        self.assertEqual(s.get_message_count("fork1"), 2)

    def test_fork_copies_messages(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "First", 5)
        s.add_message("src", "assistant", "Second", 10)
        s.fork_conversation("src", "fork1")
        self.assertEqual(s.get_messages("fork1"), s.get_messages("src"))

    def test_fork_copies_context_limit(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.set_context_limit("src", 50)
        s.fork_conversation("src", "fork1")
        # Fork inherits limit; add large message to fork — should be enforced
        s.add_message("src", "user", "Msg", 10)
        s.fork_conversation("src", "fork2")
        # Verify fork2 has the limit by adding something too big
        drops = s.add_message_with_budget("fork2", "user", "Big", 45)
        # 10 existing + 45 new = 55 > 50; should drop 1
        self.assertEqual(drops, 1)

    def test_fork_copies_user_id(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.fork_conversation("src", "fork1")
        # fork1 should be owned by alice
        self.assertIn("fork1", s.list_user_conversations("alice"))

    def test_fork_empty_conv(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        self.assertTrue(s.fork_conversation("src", "fork1"))
        self.assertEqual(s.get_message_count("fork1"), 0)


class TestLevel4BranchAtMessage(unittest.TestCase):

    def test_branch_basic(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "A", 5)
        s.add_message("src", "assistant", "B", 10)
        s.add_message("src", "user", "C", 8)
        self.assertTrue(s.branch_at_message("src", 1, "branch1"))
        self.assertEqual(s.get_message_count("branch1"), 2)
        self.assertEqual(s.get_messages("branch1"), ["user:A", "assistant:B"])

    def test_branch_at_index_zero(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "Only first", 5)
        s.add_message("src", "assistant", "Ignored", 10)
        self.assertTrue(s.branch_at_message("src", 0, "branch1"))
        self.assertEqual(s.get_messages("branch1"), ["user:Only first"])

    def test_branch_invalid_index_negative(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "A", 5)
        self.assertFalse(s.branch_at_message("src", -1, "branch1"))

    def test_branch_invalid_index_out_of_bounds(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "A", 5)
        self.assertFalse(s.branch_at_message("src", 5, "branch1"))

    def test_branch_missing_source(self):
        s = ConversationService()
        self.assertFalse(s.branch_at_message("ghost", 0, "branch1"))

    def test_branch_new_id_exists(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "A", 5)
        s.create_conversation("branch1", "alice")
        self.assertFalse(s.branch_at_message("src", 0, "branch1"))

    def test_branch_recomputes_total_tokens(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "A", 10)
        s.add_message("src", "assistant", "B", 20)
        s.add_message("src", "user", "C", 30)  # total = 60
        s.branch_at_message("src", 1, "branch1")  # keep [A, B] = 30 tokens
        # Verify by checking get_user_total_tokens
        # branch1 should have 30 tokens (10+20)
        self.assertEqual(s.get_user_total_tokens("alice"), 90)  # src=60, branch1=30

    def test_branch_independence(self):
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "A", 5)
        s.add_message("src", "assistant", "B", 10)
        s.branch_at_message("src", 0, "branch1")
        # Add to src — branch unaffected
        s.add_message("src", "user", "C", 8)
        self.assertEqual(s.get_message_count("branch1"), 1)


class TestLevel4MergeConversations(unittest.TestCase):

    def test_merge_basic(self):
        s = ConversationService()
        s.create_conversation("a", "alice")
        s.create_conversation("b", "alice")
        s.add_message("a", "user", "From A", 5)
        s.add_message("b", "user", "From B", 10)
        self.assertTrue(s.merge_conversations("a", "b"))
        # Both messages now in 'a' sorted by ts
        msgs = s.get_messages("a")
        self.assertIn("user:From A", msgs)
        self.assertIn("user:From B", msgs)

    def test_merge_absorbed_deleted(self):
        s = ConversationService()
        s.create_conversation("a", "alice")
        s.create_conversation("b", "alice")
        s.add_message("b", "user", "Hi", 5)
        s.merge_conversations("a", "b")
        self.assertEqual(s.get_message_count("b"), -1)  # deleted

    def test_merge_same_id_returns_false(self):
        s = ConversationService()
        s.create_conversation("a", "alice")
        self.assertFalse(s.merge_conversations("a", "a"))

    def test_merge_missing_survivor(self):
        s = ConversationService()
        s.create_conversation("b", "alice")
        self.assertFalse(s.merge_conversations("ghost", "b"))

    def test_merge_missing_absorbed(self):
        s = ConversationService()
        s.create_conversation("a", "alice")
        self.assertFalse(s.merge_conversations("a", "ghost"))

    def test_merge_chronological_order_by_ts(self):
        s = ConversationService()
        s.create_conversation("a", "alice")
        s.create_conversation("b", "alice")
        # ts ordering: a gets ts=1, b gets ts=2, a gets ts=3
        s.add_message("a", "user", "First", 5)
        s.add_message("b", "user", "Second", 10)
        s.add_message("a", "assistant", "Third", 8)
        s.merge_conversations("a", "b")
        msgs = s.get_messages("a")
        self.assertEqual(msgs, ["user:First", "user:Second", "assistant:Third"])

    def test_merge_with_context_limit_drops_oldest(self):
        s = ConversationService()
        s.create_conversation("a", "alice")
        s.create_conversation("b", "alice")
        s.add_message("a", "user", "A1", 10)
        s.add_message("b", "user", "B1", 10)
        s.set_context_limit("a", 15)
        # After merge: A1(10) + B1(10) = 20 > 15; drop A1
        s.merge_conversations("a", "b")
        self.assertEqual(s.get_message_count("a"), 1)
        self.assertEqual(s.get_messages("a"), ["user:B1"])

    def test_merge_survivor_keeps_owner(self):
        s = ConversationService()
        s.create_conversation("a", "alice")
        s.create_conversation("b", "bob")
        s.merge_conversations("a", "b")
        # Survivor 'a' owned by alice; check alice's conversations include 'a'
        self.assertIn("a", s.list_user_conversations("alice"))

    def test_merge_empty_absorbed(self):
        s = ConversationService()
        s.create_conversation("a", "alice")
        s.create_conversation("b", "alice")
        s.add_message("a", "user", "Hello", 10)
        self.assertTrue(s.merge_conversations("a", "b"))
        self.assertEqual(s.get_message_count("a"), 1)


if __name__ == "__main__":
    unittest.main()
