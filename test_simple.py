import unittest
from runtime.dispatcher import predict, health_check

class SimpleTest(unittest.TestCase):
    def test_health_check(self):
        result = health_check()
        self.assertEqual(result["status"], "healthy")

if __name__ == "__main__":
    unittest.main()
