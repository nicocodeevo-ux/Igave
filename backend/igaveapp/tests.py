from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from igaveapp.models import Receipt
from datetime import date


class BasicTest(TestCase):
    def test_basic_addition(self):
        self.assertEqual(1 + 1, 2)


class UserTest(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(username='testuser', password='password')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('password'))


class ReceiptTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='receiptuser', password='password')

    def test_receipt_creation(self):
        receipt = Receipt.objects.create(
            user=self.user,
            store_name="Test Store",
            date=date.today(),
            total_amount=100.50
        )
        self.assertEqual(receipt.store_name, "Test Store")
        self.assertEqual(receipt.total_amount, 100.50)
        self.assertEqual(receipt.user, self.user)


class APIAuthenticationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            password='testpass123',
            email='api@test.com'
        )

    def test_obtain_token(self):
        """Test JWT token generation."""
        response = self.client.post('/api/token/', {
            'username': 'apiuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        response = self.client.post('/api/token/', {
            'username': 'apiuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReceiptAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='receiptapiuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_receipt(self):
        """Test creating a receipt via API."""
        data = {
            'store_name': 'API Store',
            'date': date.today().isoformat(),
            'total_amount': '250.75'
        }
        response = self.client.post('/api/receipts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Receipt.objects.count(), 1)
        self.assertEqual(Receipt.objects.get().store_name, 'API Store')

    def test_list_receipts(self):
        """Test listing receipts for authenticated user."""
        Receipt.objects.create(
            user=self.user,
            store_name='Store 1',
            date=date.today(),
            total_amount=100.00
        )
        Receipt.objects.create(
            user=self.user,
            store_name='Store 2',
            date=date.today(),
            total_amount=200.00
        )
        response = self.client.get('/api/receipts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_receipt_isolation(self):
        """Test that users can only see their own receipts."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        Receipt.objects.create(
            user=other_user,
            store_name='Other Store',
            date=date.today(),
            total_amount=300.00
        )
        response = self.client.get('/api/receipts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access receipts."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/receipts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_receipt_invalid_data(self):
        """Test creating a receipt with invalid data."""
        # Missing required fields
        response = self.client.post('/api/receipts/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Invalid date format
        data = {
            'store_name': 'Invalid Date Store',
            'date': 'not-a-date',
            'total_amount': '100.00'
        }
        response = self.client.post('/api/receipts/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid amount (non-numeric)
        data = {
            'store_name': 'Invalid Amount Store',
            'date': date.today().isoformat(),
            'total_amount': 'not-a-number'
        }
        response = self.client.post('/api/receipts/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_receipt(self):
        """Test updating a receipt."""
        receipt = Receipt.objects.create(
            user=self.user,
            store_name='Original Store',
            date=date.today(),
            total_amount=100.00
        )
        url = f'/api/receipts/{receipt.id}/'
        data = {
            'store_name': 'Updated Store',
            'date': date.today().isoformat(),
            'total_amount': '150.00'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        receipt.refresh_from_db()
        self.assertEqual(receipt.store_name, 'Updated Store')
        self.assertEqual(receipt.total_amount, 150.00)

    def test_delete_receipt(self):
        """Test deleting a receipt."""
        receipt = Receipt.objects.create(
            user=self.user,
            store_name='To Delete',
            date=date.today(),
            total_amount=50.00
        )
        url = f'/api/receipts/{receipt.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Receipt.objects.count(), 0)

    def test_update_other_user_receipt(self):
        """Test that a user cannot update another user's receipt."""
        other_user = User.objects.create_user(username='other', password='password')
        receipt = Receipt.objects.create(
            user=other_user,
            store_name='Other User Receipt',
            date=date.today(),
            total_amount=100.00
        )
        url = f'/api/receipts/{receipt.id}/'
        data = {
            'store_name': 'Hacked Store',
            'date': date.today().isoformat(),
            'total_amount': '0.00'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        receipt.refresh_from_db()
        self.assertEqual(receipt.store_name, 'Other User Receipt')

    def test_delete_other_user_receipt(self):
        """Test that a user cannot delete another user's receipt."""
        other_user = User.objects.create_user(username='other', password='password')
        receipt = Receipt.objects.create(
            user=other_user,
            store_name='Other User Receipt',
            date=date.today(),
            total_amount=100.00
        )
        url = f'/api/receipts/{receipt.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Receipt.objects.count(), 1)

    def test_edge_cases(self):
        """Test edge cases for receipt creation."""
        # Max length store name
        long_name = 'A' * 100
        data = {
            'store_name': long_name,
            'date': date.today().isoformat(),
            'total_amount': '10.00'
        }
        response = self.client.post('/api/receipts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Exceeding max length
        too_long_name = 'A' * 101
        data['store_name'] = too_long_name
        response = self.client.post('/api/receipts/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
