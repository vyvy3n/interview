"""
Level 1 tests — Basic Conversation Lifecycle
Run: python3 test_level1.py
"""

import unittest
from solution import ConversationService


class TestLevel1CreateConversation(unittest.TestCase):

    def test_create_returns_true_for_new(self):
        s = ConversationService()
        self.assertTrue(s.create_conversation("c1", "alice"))

    def test_create_multiple_conversations(self):
        s = ConversationService()
        self.assertTrue(s.create_conversation("c1", "alice"))
        self.assertTrue(s.create_conversation("c2", "bob"))
        self.assertTrue(s.create_conversation("c3", "alice"))

    def test_create_duplicate_returns_false(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        self.assertFalse(s.create_conversation("c1", "alice"))

    def test_create_duplicate_different_user_returns_false(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        self.assertFalse(s.create_conversation("c1", "bob"))

    def test_create_does_not_reset_existing(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 5)
        s.create_conversation("c1", "alice")  # no-op
        self.assertEqual(s.get_message_count("c1"), 1)

    def test_create_returns_bool(self):
        s = ConversationService()
        result = s.create_conversation("c1", "alice")
        self.assertIsInstance(result, bool)


class TestLevel1AddMessage(unittest.TestCase):

    def test_add_message_returns_cumulative_tokens(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        self.assertEqual(s.add_message("c1", "user", "Hello", 5), 5)

    def test_add_message_accumulates_tokens(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 5)
        result = s.add_message("c1", "assistant", "Hi there!", 10)
        self.assertEqual(result, 15)

    def test_add_message_missing_conv_returns_neg_one(self):
        s = ConversationService()
        self.assertEqual(s.add_message("ghost", "user", "Hello", 5), -1)

    def test_add_message_missing_no_side_effect(self):
        s = ConversationService()
        s.add_message("ghost", "user", "Hello", 5)
        self.assertEqual(s.get_message_count("ghost"), -1)

    def test_add_message_multiple_accumulation(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 10)
        s.add_message("c1", "assistant", "Hi!", 8)
        s.add_message("c1", "user", "How are you?", 12)
        self.assertEqual(s.add_message("c1", "assistant", "Great!", 6), 36)

    def test_add_message_preserves_role_and_content(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "My message", 5)
        msgs = s.get_messages("c1")
        self.assertEqual(msgs[0], "user:My message")


class TestLevel1GetMessages(unittest.TestCase):

    def test_get_messages_empty_conv(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        self.assertEqual(s.get_messages("c1"), [])

    def test_get_messages_missing_conv(self):
        s = ConversationService()
        self.assertEqual(s.get_messages("ghost"), [])

    def test_get_messages_single(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello!", 5)
        self.assertEqual(s.get_messages("c1"), ["user:Hello!"])

    def test_get_messages_chronological_order(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "First", 5)
        s.add_message("c1", "assistant", "Second", 10)
        s.add_message("c1", "user", "Third", 8)
        self.assertEqual(s.get_messages("c1"), ["user:First", "assistant:Second", "user:Third"])

    def test_get_messages_format_colon_separator(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "assistant", "I'm here to help", 10)
        msgs = s.get_messages("c1")
        self.assertEqual(msgs[0], "assistant:I'm here to help")

    def test_get_messages_returns_list(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        result = s.get_messages("c1")
        self.assertIsInstance(result, list)


class TestLevel1GetMessageCount(unittest.TestCase):

    def test_get_count_empty_conv(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        self.assertEqual(s.get_message_count("c1"), 0)

    def test_get_count_missing_conv(self):
        s = ConversationService()
        self.assertEqual(s.get_message_count("ghost"), -1)

    def test_get_count_after_adds(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 5)
        s.add_message("c1", "assistant", "Hi", 10)
        self.assertEqual(s.get_message_count("c1"), 2)

    def test_empty_not_same_as_missing(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        self.assertEqual(s.get_message_count("c1"), 0)
        self.assertEqual(s.get_message_count("missing"), -1)


class TestLevel1DeleteConversation(unittest.TestCase):

    def test_delete_existing_returns_true(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        self.assertTrue(s.delete_conversation("c1"))

    def test_delete_missing_returns_false(self):
        s = ConversationService()
        self.assertFalse(s.delete_conversation("ghost"))

    def test_delete_twice_returns_false_second_time(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.delete_conversation("c1")
        self.assertFalse(s.delete_conversation("c1"))

    def test_delete_removes_messages(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 5)
        s.delete_conversation("c1")
        self.assertEqual(s.get_messages("c1"), [])
        self.assertEqual(s.get_message_count("c1"), -1)

    def test_delete_allows_recreate(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Old message", 10)
        s.delete_conversation("c1")
        # Recreate fresh
        self.assertTrue(s.create_conversation("c1", "bob"))
        self.assertEqual(s.get_message_count("c1"), 0)

    def test_delete_does_not_affect_other_convs(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.create_conversation("c2", "alice")
        s.add_message("c2", "user", "Still here", 5)
        s.delete_conversation("c1")
        self.assertEqual(s.get_message_count("c2"), 1)


if __name__ == "__main__":
    unittest.main()
