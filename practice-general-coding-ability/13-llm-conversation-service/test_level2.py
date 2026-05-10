"""
Level 2 tests — User-level Activity Reports
Run: python3 test_level2.py
"""

import unittest
from solution import ConversationService


class TestLevel2ListUserConversations(unittest.TestCase):

    def test_list_single_user(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        self.assertEqual(s.list_user_conversations("alice"), ["c1"])

    def test_list_multiple_conversations_sorted(self):
        s = ConversationService()
        s.create_conversation("zebra", "alice")
        s.create_conversation("apple", "alice")
        s.create_conversation("mango", "alice")
        self.assertEqual(s.list_user_conversations("alice"), ["apple", "mango", "zebra"])

    def test_list_only_user_convs(self):
        s = ConversationService()
        s.create_conversation("alice-1", "alice")
        s.create_conversation("bob-1", "bob")
        s.create_conversation("alice-2", "alice")
        result = s.list_user_conversations("alice")
        self.assertEqual(result, ["alice-1", "alice-2"])
        self.assertNotIn("bob-1", result)

    def test_list_unknown_user_returns_empty(self):
        s = ConversationService()
        self.assertEqual(s.list_user_conversations("carol"), [])

    def test_list_after_delete(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.create_conversation("c2", "alice")
        s.delete_conversation("c1")
        self.assertEqual(s.list_user_conversations("alice"), ["c2"])

    def test_list_returns_list(self):
        s = ConversationService()
        result = s.list_user_conversations("alice")
        self.assertIsInstance(result, list)


class TestLevel2TopKActive(unittest.TestCase):

    def test_top_k_basic(self):
        s = ConversationService()
        s.create_conversation("c1", "u1")
        s.create_conversation("c2", "u1")
        s.add_message("c1", "user", "Hello", 5)
        s.add_message("c1", "assistant", "Hi", 5)
        s.add_message("c2", "user", "Hey", 5)
        result = s.top_k_active(2)
        self.assertEqual(result, [("c1", 2), ("c2", 1)])

    def test_top_k_fewer_than_k(self):
        s = ConversationService()
        s.create_conversation("c1", "u1")
        s.add_message("c1", "user", "Hi", 5)
        result = s.top_k_active(10)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ("c1", 1))

    def test_top_k_descending_order(self):
        s = ConversationService()
        s.create_conversation("low", "u1")
        s.create_conversation("high", "u1")
        for _ in range(5):
            s.add_message("high", "user", "msg", 1)
        s.add_message("low", "user", "msg", 1)
        result = s.top_k_active(2)
        self.assertEqual(result[0][0], "high")
        self.assertEqual(result[1][0], "low")

    def test_top_k_tie_breaking_alphabetical(self):
        s = ConversationService()
        s.create_conversation("zebra", "u1")
        s.create_conversation("apple", "u1")
        s.create_conversation("mango", "u1")
        # All have 0 messages — tied; alphabetical order
        result = s.top_k_active(3)
        self.assertEqual(result, [("apple", 0), ("mango", 0), ("zebra", 0)])

    def test_top_k_empty_service(self):
        s = ConversationService()
        self.assertEqual(s.top_k_active(5), [])

    def test_top_k_returns_tuples(self):
        s = ConversationService()
        s.create_conversation("c1", "u1")
        result = s.top_k_active(1)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(len(result[0]), 2)

    def test_top_k_correct_message_count_after_adds(self):
        s = ConversationService()
        s.create_conversation("c1", "u1")
        for _ in range(7):
            s.add_message("c1", "user", "msg", 1)
        result = s.top_k_active(1)
        self.assertEqual(result[0], ("c1", 7))

    def test_top_k_tie_in_middle(self):
        s = ConversationService()
        s.create_conversation("aaa", "u1")
        s.create_conversation("bbb", "u1")
        s.create_conversation("ccc", "u1")
        s.add_message("aaa", "user", "msg", 1)
        s.add_message("aaa", "user", "msg", 1)
        # bbb and ccc both have 0 messages — tied
        result = s.top_k_active(3)
        self.assertEqual(result[0], ("aaa", 2))
        self.assertEqual(result[1], ("bbb", 0))
        self.assertEqual(result[2], ("ccc", 0))


class TestLevel2GetUserTotalTokens(unittest.TestCase):

    def test_single_conv_tokens(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 10)
        s.add_message("c1", "assistant", "Hi", 15)
        self.assertEqual(s.get_user_total_tokens("alice"), 25)

    def test_multiple_convs_tokens_summed(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.create_conversation("c2", "alice")
        s.add_message("c1", "user", "Hello", 10)
        s.add_message("c2", "user", "Hey", 5)
        self.assertEqual(s.get_user_total_tokens("alice"), 15)

    def test_unknown_user_returns_neg_one(self):
        s = ConversationService()
        self.assertEqual(s.get_user_total_tokens("nobody"), -1)

    def test_user_with_empty_convs_returns_zero(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        # No messages added — 0 tokens
        self.assertEqual(s.get_user_total_tokens("alice"), 0)

    def test_only_counts_user_convs(self):
        s = ConversationService()
        s.create_conversation("alice-1", "alice")
        s.create_conversation("bob-1", "bob")
        s.add_message("alice-1", "user", "Hello", 20)
        s.add_message("bob-1", "user", "Hi", 100)
        self.assertEqual(s.get_user_total_tokens("alice"), 20)

    def test_tokens_after_delete(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.create_conversation("c2", "alice")
        s.add_message("c1", "user", "Hello", 30)
        s.add_message("c2", "user", "Hey", 20)
        s.delete_conversation("c1")
        # Only c2 remains
        self.assertEqual(s.get_user_total_tokens("alice"), 20)

    def test_tokens_after_all_convs_deleted(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 30)
        s.delete_conversation("c1")
        self.assertEqual(s.get_user_total_tokens("alice"), -1)


if __name__ == "__main__":
    unittest.main()
