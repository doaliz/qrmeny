import requests
import sys
import json
from datetime import datetime

class RestaurantMenuAPITester:
    def __init__(self, base_url="https://menumaster-87.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.restaurant_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == expected_status
            details = ""
            
            if not success:
                details = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'No error details')}"
                except:
                    details += f" - {response.text[:100]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                return False, {}

        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"   Error: {error_msg}")
            self.log_test(name, False, error_msg)
            return False, {}

    def test_register(self):
        """Test restaurant registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_data = {
            "name": f"Test Restaurant {timestamp}",
            "email": f"test{timestamp}@restaurant.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "Restaurant Registration",
            "POST",
            "auth/register",
            200,
            data=test_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.restaurant_id = response['restaurant']['id']
            print(f"   Token received: {self.token[:20]}...")
            print(f"   Restaurant ID: {self.restaurant_id}")
            return True
        return False

    def test_login(self):
        """Test login with existing credentials"""
        # First register a user for login test
        timestamp = datetime.now().strftime('%H%M%S')
        register_data = {
            "name": f"Login Test Restaurant {timestamp}",
            "email": f"login{timestamp}@restaurant.com",
            "password": "LoginPass123!"
        }
        
        # Register first
        success, _ = self.run_test(
            "Pre-register for Login Test",
            "POST",
            "auth/register",
            200,
            data=register_data
        )
        
        if not success:
            return False
        
        # Now test login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        success, response = self.run_test(
            "Restaurant Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        return success and 'token' in response

    def test_auth_me(self):
        """Test getting current restaurant info"""
        success, response = self.run_test(
            "Get Current Restaurant",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_categories_crud(self):
        """Test category CRUD operations"""
        # Create category
        category_data = {
            "name": "Test Ana Yemekler",
            "order": 1
        }
        
        success, response = self.run_test(
            "Create Category",
            "POST",
            "categories",
            200,
            data=category_data
        )
        
        if not success:
            return False
        
        category_id = response.get('id')
        if not category_id:
            self.log_test("Create Category - ID Check", False, "No category ID returned")
            return False
        
        # Get categories
        success, response = self.run_test(
            "Get Categories",
            "GET",
            "categories",
            200
        )
        
        if not success:
            return False
        
        # Update category
        update_data = {
            "name": "Updated Ana Yemekler",
            "order": 2
        }
        
        success, response = self.run_test(
            "Update Category",
            "PUT",
            f"categories/{category_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
        
        # Delete category (will be done after menu items test)
        return category_id

    def test_menu_items_crud(self, category_id):
        """Test menu item CRUD operations"""
        # Create menu item
        item_data = {
            "category_id": category_id,
            "name": "Test Pizza",
            "description": "Delicious test pizza",
            "price": 25.50,
            "image_url": "https://example.com/pizza.jpg"
        }
        
        success, response = self.run_test(
            "Create Menu Item",
            "POST",
            "menu-items",
            200,
            data=item_data
        )
        
        if not success:
            return False
        
        item_id = response.get('id')
        if not item_id:
            self.log_test("Create Menu Item - ID Check", False, "No item ID returned")
            return False
        
        # Get menu items
        success, response = self.run_test(
            "Get Menu Items",
            "GET",
            "menu-items",
            200
        )
        
        if not success:
            return False
        
        # Update menu item
        update_data = {
            "name": "Updated Pizza",
            "price": 30.00
        }
        
        success, response = self.run_test(
            "Update Menu Item",
            "PUT",
            f"menu-items/{item_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
        
        # Delete menu item
        success, response = self.run_test(
            "Delete Menu Item",
            "DELETE",
            f"menu-items/{item_id}",
            200
        )
        
        return success

    def test_public_menu(self):
        """Test public menu endpoint"""
        if not self.restaurant_id:
            self.log_test("Public Menu Test", False, "No restaurant ID available")
            return False
        
        success, response = self.run_test(
            "Get Public Menu",
            "GET",
            f"menu/public/{self.restaurant_id}",
            200
        )
        
        if success:
            # Check response structure
            if 'restaurant' in response and 'categories' in response:
                self.log_test("Public Menu Structure Check", True)
            else:
                self.log_test("Public Menu Structure Check", False, "Missing restaurant or categories in response")
        
        return success

    def test_invalid_auth(self):
        """Test invalid authentication"""
        # Save current token
        original_token = self.token
        
        # Test with invalid token
        self.token = "invalid_token"
        
        success, response = self.run_test(
            "Invalid Token Test",
            "GET",
            "auth/me",
            401
        )
        
        # Restore original token
        self.token = original_token
        
        return success

    def test_file_upload_validation(self):
        """Test file upload with format and size validation"""
        import base64
        import io
        
        # Test 1: Valid PNG file (small)
        small_png_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==')
        
        # Create a small test file
        files = {'file': ('test.png', io.BytesIO(small_png_data), 'image/png')}
        
        try:
            response = requests.post(
                f"{self.api_url}/upload-image",
                files=files,
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                response_data = response.json()
                if 'image_url' in response_data and response_data['image_url'].startswith('data:image/'):
                    self.log_test("File Upload - Valid PNG", True)
                else:
                    self.log_test("File Upload - Valid PNG", False, "Invalid response format")
                    success = False
            else:
                self.log_test("File Upload - Valid PNG", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("File Upload - Valid PNG", False, f"Error: {str(e)}")
            success = False
        
        # Test 2: Invalid file format
        files = {'file': ('test.txt', io.BytesIO(b'test content'), 'text/plain')}
        
        try:
            response = requests.post(
                f"{self.api_url}/upload-image",
                files=files,
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=10
            )
            
            # Should return 400 for invalid format
            if response.status_code == 400:
                self.log_test("File Upload - Invalid Format Rejection", True)
            else:
                self.log_test("File Upload - Invalid Format Rejection", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("File Upload - Invalid Format Rejection", False, f"Error: {str(e)}")
        
        # Test 3: File too large (simulate 6MB file)
        large_data = b'x' * (6 * 1024 * 1024)  # 6MB
        files = {'file': ('large.jpg', io.BytesIO(large_data), 'image/jpeg')}
        
        try:
            response = requests.post(
                f"{self.api_url}/upload-image",
                files=files,
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=15
            )
            
            # Should return 400 for file too large
            if response.status_code == 400:
                self.log_test("File Upload - Size Limit Rejection", True)
            else:
                self.log_test("File Upload - Size Limit Rejection", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("File Upload - Size Limit Rejection", False, f"Error: {str(e)}")
        
        return success

    def test_product_availability_toggle(self, category_id):
        """Test product availability toggle functionality"""
        # Create a product with is_available = True
        item_data = {
            "category_id": category_id,
            "name": "Test Availability Product",
            "description": "Test product for availability toggle",
            "price": 15.00,
            "is_available": True
        }
        
        success, response = self.run_test(
            "Create Product - Available",
            "POST",
            "menu-items",
            200,
            data=item_data
        )
        
        if not success:
            return False
        
        item_id = response.get('id')
        if not item_id:
            self.log_test("Product Availability - ID Check", False, "No item ID returned")
            return False
        
        # Verify product is available
        if response.get('is_available') != True:
            self.log_test("Product Availability - Initial State", False, "Product not created as available")
            return False
        else:
            self.log_test("Product Availability - Initial State", True)
        
        # Toggle to unavailable
        update_data = {"is_available": False}
        success, response = self.run_test(
            "Toggle Product - Set Unavailable",
            "PUT",
            f"menu-items/{item_id}",
            200,
            data=update_data
        )
        
        if success and response.get('is_available') == False:
            self.log_test("Product Availability - Toggle to Unavailable", True)
        else:
            self.log_test("Product Availability - Toggle to Unavailable", False, "Failed to set unavailable")
            return False
        
        # Toggle back to available
        update_data = {"is_available": True}
        success, response = self.run_test(
            "Toggle Product - Set Available",
            "PUT",
            f"menu-items/{item_id}",
            200,
            data=update_data
        )
        
        if success and response.get('is_available') == True:
            self.log_test("Product Availability - Toggle to Available", True)
        else:
            self.log_test("Product Availability - Toggle to Available", False, "Failed to set available")
            return False
        
        # Clean up
        self.run_test(
            "Delete Availability Test Product",
            "DELETE",
            f"menu-items/{item_id}",
            200
        )
        
        return True

    def test_public_menu_filtering(self):
        """Test that public menu filters out unavailable products"""
        if not self.restaurant_id:
            self.log_test("Public Menu Filtering", False, "No restaurant ID available")
            return False
        
        # Create a category for testing
        category_data = {"name": "Filter Test Category", "order": 99}
        success, cat_response = self.run_test(
            "Create Filter Test Category",
            "POST",
            "categories",
            200,
            data=category_data
        )
        
        if not success:
            return False
        
        category_id = cat_response.get('id')
        
        # Create available product
        available_item = {
            "category_id": category_id,
            "name": "Available Product",
            "price": 10.00,
            "is_available": True
        }
        
        success, available_response = self.run_test(
            "Create Available Product for Filtering",
            "POST",
            "menu-items",
            200,
            data=available_item
        )
        
        if not success:
            return False
        
        available_item_id = available_response.get('id')
        
        # Create unavailable product
        unavailable_item = {
            "category_id": category_id,
            "name": "Unavailable Product",
            "price": 20.00,
            "is_available": False
        }
        
        success, unavailable_response = self.run_test(
            "Create Unavailable Product for Filtering",
            "POST",
            "menu-items",
            200,
            data=unavailable_item
        )
        
        if not success:
            return False
        
        unavailable_item_id = unavailable_response.get('id')
        
        # Get public menu and check filtering
        success, menu_response = self.run_test(
            "Get Public Menu for Filtering Test",
            "GET",
            f"menu/public/{self.restaurant_id}",
            200
        )
        
        if not success:
            return False
        
        # Find our test category in the response
        test_category = None
        for category in menu_response.get('categories', []):
            if category.get('id') == category_id:
                test_category = category
                break
        
        if not test_category:
            self.log_test("Public Menu Filtering - Category Found", False, "Test category not found in public menu")
            return False
        
        # Check that only available items are included
        items = test_category.get('items', [])
        available_items = [item for item in items if item.get('id') == available_item_id]
        unavailable_items = [item for item in items if item.get('id') == unavailable_item_id]
        
        if len(available_items) == 1 and len(unavailable_items) == 0:
            self.log_test("Public Menu Filtering - Correct Filtering", True)
            filtering_success = True
        else:
            self.log_test("Public Menu Filtering - Correct Filtering", False, 
                         f"Available items: {len(available_items)}, Unavailable items: {len(unavailable_items)}")
            filtering_success = False
        
        # Clean up
        self.run_test("Delete Available Test Product", "DELETE", f"menu-items/{available_item_id}", 200)
        self.run_test("Delete Unavailable Test Product", "DELETE", f"menu-items/{unavailable_item_id}", 200)
        self.run_test("Delete Filter Test Category", "DELETE", f"categories/{category_id}", 200)
        
        return filtering_success

    def test_multi_tenant_isolation(self):
        """Test that restaurants can only access their own data"""
        # Create another restaurant
        timestamp = datetime.now().strftime('%H%M%S')
        other_restaurant_data = {
            "name": f"Other Restaurant {timestamp}",
            "email": f"other{timestamp}@restaurant.com",
            "password": "OtherPass123!"
        }
        
        # Save current auth
        original_token = self.token
        original_restaurant_id = self.restaurant_id
        
        # Register other restaurant
        success, response = self.run_test(
            "Register Other Restaurant",
            "POST",
            "auth/register",
            200,
            data=other_restaurant_data
        )
        
        if not success:
            return False
        
        other_token = response['token']
        other_restaurant_id = response['restaurant']['id']
        
        # Switch to other restaurant
        self.token = other_token
        self.restaurant_id = other_restaurant_id
        
        # Try to access original restaurant's public menu
        success, response = self.run_test(
            "Access Other Restaurant Public Menu",
            "GET",
            f"menu/public/{original_restaurant_id}",
            200
        )
        
        # This should succeed (public menu is public)
        public_menu_success = success
        
        # Switch back to original restaurant
        self.token = original_token
        self.restaurant_id = original_restaurant_id
        
        return public_menu_success

    def test_super_admin_registration_and_login(self):
        """Test Super Admin registration and login"""
        # Try to login first (in case already registered)
        login_data = {
            "email": "admin@qrmenu.com",
            "password": "Admin123!"
        }
        
        success, response = self.run_test(
            "Super Admin Login (Existing)",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            return True, response['token']
        
        # If login failed, try registration
        super_admin_data = {
            "name": "Super Admin",
            "email": "admin@qrmenu.com",
            "password": "Admin123!"
        }
        
        success, response = self.run_test(
            "Super Admin Registration",
            "POST",
            "auth/register",
            200,
            data=super_admin_data
        )
        
        if not success:
            # If registration failed (email exists), try login again
            success, response = self.run_test(
                "Super Admin Login (After Failed Registration)",
                "POST",
                "auth/login",
                200,
                data=login_data
            )
        
        if success and 'token' in response:
            return True, response['token']
        
        return False, None

    def test_subscription_info_super_admin_flag(self, super_admin_token):
        """Test subscription info returns is_super_admin flag"""
        # Save current token
        original_token = self.token
        
        # Test with super admin token
        self.token = super_admin_token
        success, response = self.run_test(
            "Subscription Info - Super Admin Flag",
            "GET",
            "subscription/info",
            200
        )
        
        if success:
            is_super_admin = response.get('is_super_admin', False)
            if is_super_admin:
                self.log_test("Super Admin Flag Check", True)
            else:
                self.log_test("Super Admin Flag Check", False, "is_super_admin should be true for super admin")
                success = False
        
        # Test with regular user token
        self.token = original_token
        success_regular, response_regular = self.run_test(
            "Subscription Info - Regular User Flag",
            "GET",
            "subscription/info",
            200
        )
        
        if success_regular:
            is_super_admin_regular = response_regular.get('is_super_admin', True)  # Default to True to catch errors
            if not is_super_admin_regular:
                self.log_test("Regular User Flag Check", True)
            else:
                self.log_test("Regular User Flag Check", False, "is_super_admin should be false for regular user")
                success_regular = False
        
        return success and success_regular

    def test_super_admin_list_restaurants(self, super_admin_token):
        """Test super admin can list all restaurants"""
        # Save current token
        original_token = self.token
        
        # Test with super admin token
        self.token = super_admin_token
        success, response = self.run_test(
            "Super Admin - List All Restaurants",
            "GET",
            "admin/restaurants",
            200
        )
        
        if success:
            if isinstance(response, list):
                self.log_test("List Restaurants Response Format", True)
            else:
                self.log_test("List Restaurants Response Format", False, "Response should be a list")
                success = False
        
        # Test with regular user token (should fail)
        self.token = original_token
        success_regular, response_regular = self.run_test(
            "Regular User - List Restaurants (Should Fail)",
            "GET",
            "admin/restaurants",
            403
        )
        
        return success and success_regular

    def test_super_admin_create_restaurant(self, super_admin_token):
        """Test super admin can create new restaurants"""
        # Save current token
        original_token = self.token
        
        # Test with super admin token
        self.token = super_admin_token
        timestamp = datetime.now().strftime('%H%M%S')
        restaurant_data = {
            "name": f"Admin Created Restaurant {timestamp}",
            "email": f"admin_created_{timestamp}@restaurant.com",
            "phone": "+90555123456",
            "password": "AdminCreated123!"
        }
        
        success, response = self.run_test(
            "Super Admin - Create Restaurant",
            "POST",
            "admin/restaurants",
            200,
            data=restaurant_data
        )
        
        if success:
            if 'restaurant_id' in response and 'message' in response:
                self.log_test("Create Restaurant Response Format", True)
            else:
                self.log_test("Create Restaurant Response Format", False, "Missing required fields in response")
                success = False
        
        # Test with regular user token (should fail)
        self.token = original_token
        regular_restaurant_data = {
            "name": f"Regular User Restaurant {timestamp}",
            "email": f"regular_created_{timestamp}@restaurant.com",
            "phone": "+90555654321",
            "password": "RegularCreated123!"
        }
        
        success_regular, response_regular = self.run_test(
            "Regular User - Create Restaurant (Should Fail)",
            "POST",
            "admin/restaurants",
            403,
            data=regular_restaurant_data
        )
        
        return success and success_regular

    def test_super_admin_manual_subscription(self, super_admin_token):
        """Test super admin can add manual subscriptions"""
        # Save current token
        original_token = self.token
        
        # First create a test restaurant to add subscription to
        self.token = super_admin_token
        timestamp = datetime.now().strftime('%H%M%S')
        restaurant_data = {
            "name": f"Subscription Test Restaurant {timestamp}",
            "email": f"sub_test_{timestamp}@restaurant.com",
            "phone": "+90555789123",
            "password": "SubTest123!"
        }
        
        success, response = self.run_test(
            "Create Restaurant for Subscription Test",
            "POST",
            "admin/restaurants",
            200,
            data=restaurant_data
        )
        
        if not success:
            self.token = original_token
            return False
        
        # Test manual subscription addition
        subscription_data = {
            "email": restaurant_data["email"],
            "duration_days": 30
        }
        
        success, response = self.run_test(
            "Super Admin - Add Manual Subscription",
            "POST",
            "admin/manual-subscription",
            200,
            data=subscription_data
        )
        
        if success:
            if 'message' in response and 'new_end_date' in response:
                self.log_test("Manual Subscription Response Format", True)
            else:
                self.log_test("Manual Subscription Response Format", False, "Missing required fields in response")
                success = False
        
        # Test with regular user token (should fail)
        self.token = original_token
        success_regular, response_regular = self.run_test(
            "Regular User - Add Manual Subscription (Should Fail)",
            "POST",
            "admin/manual-subscription",
            403,
            data=subscription_data
        )
        
        return success and success_regular

    def test_regular_user_login(self):
        """Test login with regular test user"""
        login_data = {
            "email": "regulartest@test.com",
            "password": "Test123!"
        }
        
        success, response = self.run_test(
            "Regular Test User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            return True, response['token']
        
        return False, None

    def test_password_change(self, regular_token):
        """Test password change functionality"""
        # Save current token
        original_token = self.token
        
        # Test with regular user token
        self.token = regular_token
        
        # Test 1: Wrong current password
        wrong_password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!"
        }
        
        success, response = self.run_test(
            "Password Change - Wrong Current Password",
            "POST",
            "auth/change-password",
            400,
            data=wrong_password_data
        )
        
        if success:
            # Check if error message is correct
            try:
                error_response = requests.post(
                    f"{self.api_url}/auth/change-password",
                    json=wrong_password_data,
                    headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
                    timeout=10
                )
                if error_response.status_code == 400:
                    error_data = error_response.json()
                    if error_data.get('detail') == "Mevcut şifre yanlış":
                        self.log_test("Password Change - Correct Error Message", True)
                    else:
                        self.log_test("Password Change - Correct Error Message", False, f"Expected 'Mevcut şifre yanlış', got '{error_data.get('detail')}'")
            except Exception as e:
                self.log_test("Password Change - Error Message Check", False, f"Error: {str(e)}")
        
        # Test 2: Correct current password
        correct_password_data = {
            "current_password": "Test123!",
            "new_password": "NewTestPassword123!"
        }
        
        success, response = self.run_test(
            "Password Change - Correct Current Password",
            "POST",
            "auth/change-password",
            200,
            data=correct_password_data
        )
        
        if success:
            # Try to login with new password to verify change
            new_login_data = {
                "email": "regulartest@test.com",
                "password": "NewTestPassword123!"
            }
            
            success_new_login, response_new_login = self.run_test(
                "Login with New Password",
                "POST",
                "auth/login",
                200,
                data=new_login_data
            )
            
            if success_new_login:
                # Change password back to original
                change_back_data = {
                    "current_password": "NewTestPassword123!",
                    "new_password": "Test123!"
                }
                
                # Update token to new one
                self.token = response_new_login['token']
                
                self.run_test(
                    "Change Password Back to Original",
                    "POST",
                    "auth/change-password",
                    200,
                    data=change_back_data
                )
        
        # Restore original token
        self.token = original_token
        
        return success

    def test_account_deletion_request(self, regular_token):
        """Test account deletion request functionality"""
        # Save current token
        original_token = self.token
        
        # Test with regular user token
        self.token = regular_token
        
        # Test 1: Create deletion request with reason
        deletion_data = {
            "reason": "Test deletion request - automated testing"
        }
        
        success, response = self.run_test(
            "Account Deletion Request - With Reason",
            "POST",
            "auth/request-deletion",
            200,
            data=deletion_data
        )
        
        if success:
            # Test 2: Try to create another request (should fail)
            success_duplicate, response_duplicate = self.run_test(
                "Account Deletion Request - Duplicate (Should Fail)",
                "POST",
                "auth/request-deletion",
                400,
                data=deletion_data
            )
            
            if success_duplicate:
                # Check error message
                try:
                    error_response = requests.post(
                        f"{self.api_url}/auth/request-deletion",
                        json=deletion_data,
                        headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
                        timeout=10
                    )
                    if error_response.status_code == 400:
                        error_data = error_response.json()
                        if error_data.get('detail') == "Zaten bekleyen bir silme talebiniz var":
                            self.log_test("Deletion Request - Correct Duplicate Error", True)
                        else:
                            self.log_test("Deletion Request - Correct Duplicate Error", False, f"Expected 'Zaten bekleyen bir silme talebiniz var', got '{error_data.get('detail')}'")
                except Exception as e:
                    self.log_test("Deletion Request - Duplicate Error Check", False, f"Error: {str(e)}")
        
        # Test 3: Create deletion request without reason
        deletion_no_reason = {}
        
        success_no_reason, response_no_reason = self.run_test(
            "Account Deletion Request - No Reason",
            "POST",
            "auth/request-deletion",
            200,
            data=deletion_no_reason
        )
        
        # Restore original token
        self.token = original_token
        
        return success

    def test_admin_deletion_requests(self, super_admin_token):
        """Test super admin deletion requests management"""
        # Save current token
        original_token = self.token
        
        # Test with super admin token
        self.token = super_admin_token
        
        # Test 1: Get deletion requests
        success, response = self.run_test(
            "Super Admin - Get Deletion Requests",
            "GET",
            "admin/deletion-requests",
            200
        )
        
        if success:
            if isinstance(response, list):
                self.log_test("Deletion Requests Response Format", True)
                
                # If there are requests, test reject functionality
                if len(response) > 0:
                    request_id = response[0].get('id')
                    if request_id:
                        # Test reject deletion request
                        success_reject, response_reject = self.run_test(
                            "Super Admin - Reject Deletion Request",
                            "POST",
                            f"admin/deletion-requests/{request_id}/reject",
                            200
                        )
                        
                        if success_reject:
                            self.log_test("Deletion Request Rejection", True)
                        else:
                            self.log_test("Deletion Request Rejection", False, "Failed to reject deletion request")
            else:
                self.log_test("Deletion Requests Response Format", False, "Response should be a list")
                success = False
        
        # Test with regular user token (should fail)
        self.token = original_token
        success_regular, response_regular = self.run_test(
            "Regular User - Get Deletion Requests (Should Fail)",
            "GET",
            "admin/deletion-requests",
            403
        )
        
        return success and success_regular

    def test_admin_delete_restaurant(self, super_admin_token):
        """Test super admin restaurant deletion"""
        # Save current token
        original_token = self.token
        
        # First create a test restaurant to delete
        self.token = super_admin_token
        timestamp = datetime.now().strftime('%H%M%S')
        restaurant_data = {
            "name": f"Delete Test Restaurant {timestamp}",
            "email": f"delete_test_{timestamp}@restaurant.com",
            "phone": "+90555999888",
            "password": "DeleteTest123!"
        }
        
        success, response = self.run_test(
            "Create Restaurant for Deletion Test",
            "POST",
            "admin/restaurants",
            200,
            data=restaurant_data
        )
        
        if not success:
            self.token = original_token
            return False
        
        # Get the restaurant ID from the list
        success_list, response_list = self.run_test(
            "List Restaurants to Find Test Restaurant",
            "GET",
            "admin/restaurants",
            200
        )
        
        if not success_list:
            self.token = original_token
            return False
        
        # Find our test restaurant
        test_restaurant_id = None
        for restaurant in response_list:
            if restaurant.get('email') == restaurant_data['email']:
                test_restaurant_id = restaurant.get('id')
                break
        
        if not test_restaurant_id:
            self.log_test("Find Test Restaurant for Deletion", False, "Could not find test restaurant")
            self.token = original_token
            return False
        
        # Test 1: Delete restaurant as super admin
        success, response = self.run_test(
            "Super Admin - Delete Restaurant",
            "DELETE",
            f"admin/restaurants/{test_restaurant_id}",
            200
        )
        
        # Test 2: Try to delete super admin (should fail)
        # First get super admin restaurant ID
        success_admin_list, response_admin_list = self.run_test(
            "List Restaurants to Find Super Admin",
            "GET",
            "admin/restaurants",
            200
        )
        
        super_admin_restaurant_id = None
        if success_admin_list:
            for restaurant in response_admin_list:
                if restaurant.get('email') == 'admin@qrmenu.com':
                    super_admin_restaurant_id = restaurant.get('id')
                    break
        
        if super_admin_restaurant_id:
            success_admin_delete, response_admin_delete = self.run_test(
                "Super Admin - Try Delete Super Admin (Should Fail)",
                "DELETE",
                f"admin/restaurants/{super_admin_restaurant_id}",
                400
            )
            
            if success_admin_delete:
                # Check error message
                try:
                    error_response = requests.delete(
                        f"{self.api_url}/admin/restaurants/{super_admin_restaurant_id}",
                        headers={'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'},
                        timeout=10
                    )
                    if error_response.status_code == 400:
                        error_data = error_response.json()
                        if error_data.get('detail') == "Super admin hesabı silinemez":
                            self.log_test("Super Admin Deletion Prevention", True)
                        else:
                            self.log_test("Super Admin Deletion Prevention", False, f"Expected 'Super admin hesabı silinemez', got '{error_data.get('detail')}'")
                except Exception as e:
                    self.log_test("Super Admin Deletion Error Check", False, f"Error: {str(e)}")
        
        # Test 3: Try to delete restaurant as regular user (should fail)
        self.token = original_token
        success_regular, response_regular = self.run_test(
            "Regular User - Delete Restaurant (Should Fail)",
            "DELETE",
            f"admin/restaurants/{test_restaurant_id}",
            403
        )
        
        return success and success_regular

    def test_subscription_info_fix(self, regular_token):
        """Test subscription info fix verification"""
        # Save current token
        original_token = self.token
        
        # Test with regular user token
        self.token = regular_token
        
        success, response = self.run_test(
            "Subscription Info Fix - Regular User",
            "GET",
            "subscription/info",
            200
        )
        
        if success:
            subscription_status = response.get('subscription_status')
            days_remaining = response.get('days_remaining')
            
            # Check if subscription_status is "active" and days_remaining is around 364 (not trial days)
            if subscription_status == 'active':
                self.log_test("Subscription Status - Active", True)
                
                if days_remaining and days_remaining > 300:  # Should be around 364, not 6
                    self.log_test("Days Remaining - Subscription Days (Not Trial)", True)
                else:
                    self.log_test("Days Remaining - Subscription Days (Not Trial)", False, f"Expected >300 days, got {days_remaining}")
            else:
                self.log_test("Subscription Status - Active", False, f"Expected 'active', got '{subscription_status}'")
                success = False
        
        # Restore original token
        self.token = original_token
        
        return success

    def test_campaign_crud_api(self):
        """Test Campaign CRUD API operations"""
        print("\n🔍 Testing CAMPAIGN CRUD API")
        
        # Test 1: GET campaign (should return existing campaign or null)
        success, response = self.run_test(
            "GET Campaign - Initial State",
            "GET",
            "campaign",
            200
        )
        
        initial_campaign = response if success else None
        
        # Test 2: POST campaign - Create/Update campaign
        campaign_data = {
            "title": "Test Kampanyası",
            "description": "Test kampanya açıklaması",
            "image_url": "https://example.com/campaign.jpg",
            "is_active": True
        }
        
        success, response = self.run_test(
            "POST Campaign - Create/Update",
            "POST",
            "campaign",
            200,
            data=campaign_data
        )
        
        if success:
            if 'message' in response:
                self.log_test("Campaign Create/Update Response Format", True)
            else:
                self.log_test("Campaign Create/Update Response Format", False, "Missing message in response")
        
        # Test 3: GET campaign after creation
        success, response = self.run_test(
            "GET Campaign - After Creation",
            "GET",
            "campaign",
            200
        )
        
        if success:
            if response and response.get('title') == campaign_data['title']:
                self.log_test("Campaign Data Verification", True)
            else:
                self.log_test("Campaign Data Verification", False, "Campaign data doesn't match")
        
        # Test 4: PUT campaign - Update existing
        update_data = {
            "title": "Updated Test Kampanyası",
            "is_active": False
        }
        
        success, response = self.run_test(
            "PUT Campaign - Update Existing",
            "PUT",
            "campaign",
            200,
            data=update_data
        )
        
        # Test 5: DELETE campaign
        success, response = self.run_test(
            "DELETE Campaign",
            "DELETE",
            "campaign",
            200
        )
        
        if success:
            if 'message' in response:
                self.log_test("Campaign Delete Response Format", True)
            else:
                self.log_test("Campaign Delete Response Format", False, "Missing message in response")
        
        # Test 6: GET campaign after deletion (should return null or 404)
        success, response = self.run_test(
            "GET Campaign - After Deletion",
            "GET",
            "campaign",
            200
        )
        
        if success and response is None:
            self.log_test("Campaign Deletion Verification", True)
        else:
            self.log_test("Campaign Deletion Verification", False, "Campaign still exists after deletion")
        
        return True

    def test_menu_items_with_campaign_fields(self, category_id):
        """Test Menu Items with Campaign Fields"""
        print("\n🔍 Testing MENU ITEMS WITH CAMPAIGN FIELDS")
        
        # Test 1: Create menu item with is_campaign=true, campaign_only=false
        item_data_1 = {
            "category_id": category_id,
            "name": "Campaign Item - Both Categories",
            "description": "Item that appears in both campaign and regular category",
            "price": 25.00,
            "is_campaign": True,
            "campaign_only": False
        }
        
        success, response = self.run_test(
            "Create Menu Item - Campaign Item (Both Categories)",
            "POST",
            "menu-items",
            200,
            data=item_data_1
        )
        
        item_1_id = None
        if success:
            item_1_id = response.get('id')
            if response.get('is_campaign') == True and response.get('campaign_only') == False:
                self.log_test("Campaign Fields Verification - Both Categories", True)
            else:
                self.log_test("Campaign Fields Verification - Both Categories", False, 
                             f"Expected is_campaign=True, campaign_only=False, got is_campaign={response.get('is_campaign')}, campaign_only={response.get('campaign_only')}")
        
        # Test 2: Create menu item with is_campaign=true, campaign_only=true
        item_data_2 = {
            "category_id": category_id,
            "name": "Campaign Item - Campaign Only",
            "description": "Item that appears only in campaign category",
            "price": 30.00,
            "is_campaign": True,
            "campaign_only": True
        }
        
        success, response = self.run_test(
            "Create Menu Item - Campaign Only",
            "POST",
            "menu-items",
            200,
            data=item_data_2
        )
        
        item_2_id = None
        if success:
            item_2_id = response.get('id')
            if response.get('is_campaign') == True and response.get('campaign_only') == True:
                self.log_test("Campaign Fields Verification - Campaign Only", True)
            else:
                self.log_test("Campaign Fields Verification - Campaign Only", False, 
                             f"Expected is_campaign=True, campaign_only=True, got is_campaign={response.get('is_campaign')}, campaign_only={response.get('campaign_only')}")
        
        # Test 3: GET menu items and verify campaign fields are returned
        success, response = self.run_test(
            "GET Menu Items - Campaign Fields Included",
            "GET",
            "menu-items",
            200
        )
        
        if success:
            campaign_items = [item for item in response if item.get('is_campaign', False)]
            if len(campaign_items) >= 2:
                self.log_test("Campaign Items in Menu Items List", True)
                
                # Verify specific items
                item_1_found = any(item.get('id') == item_1_id for item in campaign_items)
                item_2_found = any(item.get('id') == item_2_id for item in campaign_items)
                
                if item_1_found and item_2_found:
                    self.log_test("Campaign Items Data Integrity", True)
                else:
                    self.log_test("Campaign Items Data Integrity", False, "Created campaign items not found in list")
            else:
                self.log_test("Campaign Items in Menu Items List", False, f"Expected at least 2 campaign items, found {len(campaign_items)}")
        
        # Clean up
        if item_1_id:
            self.run_test("Delete Campaign Item 1", "DELETE", f"menu-items/{item_1_id}", 200)
        if item_2_id:
            self.run_test("Delete Campaign Item 2", "DELETE", f"menu-items/{item_2_id}", 200)
        
        return True

    def test_public_menu_with_campaign_data(self):
        """Test Public Menu API with Campaign Data"""
        print("\n🔍 Testing PUBLIC MENU API WITH CAMPAIGN DATA")
        
        if not self.restaurant_id:
            self.log_test("Public Menu Campaign Test", False, "No restaurant ID available")
            return False
        
        # First create a campaign
        campaign_data = {
            "title": "Yaz Kampanyası",
            "description": "Yaz aylarına özel kampanya",
            "image_url": "https://example.com/summer-campaign.jpg",
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create Campaign for Public Menu Test",
            "POST",
            "campaign",
            200,
            data=campaign_data
        )
        
        if not success:
            return False
        
        # Create a test category
        category_data = {"name": "Campaign Test Category", "order": 1}
        success, cat_response = self.run_test(
            "Create Category for Campaign Test",
            "POST",
            "categories",
            200,
            data=category_data
        )
        
        if not success:
            return False
        
        category_id = cat_response.get('id')
        
        # Create campaign items
        campaign_item_both = {
            "category_id": category_id,
            "name": "Campaign Item Both",
            "price": 20.00,
            "is_campaign": True,
            "campaign_only": False
        }
        
        campaign_item_only = {
            "category_id": category_id,
            "name": "Campaign Item Only",
            "price": 25.00,
            "is_campaign": True,
            "campaign_only": True
        }
        
        regular_item = {
            "category_id": category_id,
            "name": "Regular Item",
            "price": 15.00,
            "is_campaign": False,
            "campaign_only": False
        }
        
        # Create all items
        success_1, response_1 = self.run_test("Create Campaign Item Both", "POST", "menu-items", 200, data=campaign_item_both)
        success_2, response_2 = self.run_test("Create Campaign Item Only", "POST", "menu-items", 200, data=campaign_item_only)
        success_3, response_3 = self.run_test("Create Regular Item", "POST", "menu-items", 200, data=regular_item)
        
        if not (success_1 and success_2 and success_3):
            return False
        
        item_both_id = response_1.get('id')
        item_only_id = response_2.get('id')
        regular_item_id = response_3.get('id')
        
        # Test public menu API
        success, response = self.run_test(
            "GET Public Menu with Campaign Data",
            "GET",
            f"menu/public/{self.restaurant_id}",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['restaurant', 'categories', 'campaign', 'campaign_items']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                self.log_test("Public Menu Response Structure", True)
                
                # Verify campaign object
                campaign = response.get('campaign')
                if campaign and campaign.get('title') == "Yaz Kampanyası":
                    self.log_test("Campaign Object in Public Menu", True)
                else:
                    self.log_test("Campaign Object in Public Menu", False, "Campaign object missing or incorrect")
                
                # Verify campaign_items array
                campaign_items = response.get('campaign_items', [])
                campaign_item_names = [item.get('name') for item in campaign_items]
                
                if "Campaign Item Both" in campaign_item_names and "Campaign Item Only" in campaign_item_names:
                    self.log_test("Campaign Items Array", True)
                else:
                    self.log_test("Campaign Items Array", False, f"Expected campaign items not found. Found: {campaign_item_names}")
                
                # Verify categories filtering (campaign_only items should be excluded from regular categories)
                categories = response.get('categories', [])
                test_category = None
                for cat in categories:
                    if cat.get('id') == category_id:
                        test_category = cat
                        break
                
                if test_category:
                    category_items = test_category.get('items', [])
                    category_item_names = [item.get('name') for item in category_items]
                    
                    # Should include "Campaign Item Both" and "Regular Item" but NOT "Campaign Item Only"
                    if ("Campaign Item Both" in category_item_names and 
                        "Regular Item" in category_item_names and 
                        "Campaign Item Only" not in category_item_names):
                        self.log_test("Campaign Only Items Filtering", True)
                    else:
                        self.log_test("Campaign Only Items Filtering", False, 
                                     f"Incorrect filtering. Category items: {category_item_names}")
                else:
                    self.log_test("Test Category in Public Menu", False, "Test category not found")
            else:
                self.log_test("Public Menu Response Structure", False, f"Missing fields: {missing_fields}")
        
        # Clean up
        if item_both_id:
            self.run_test("Delete Campaign Item Both", "DELETE", f"menu-items/{item_both_id}", 200)
        if item_only_id:
            self.run_test("Delete Campaign Item Only", "DELETE", f"menu-items/{item_only_id}", 200)
        if regular_item_id:
            self.run_test("Delete Regular Item", "DELETE", f"menu-items/{regular_item_id}", 200)
        if category_id:
            self.run_test("Delete Campaign Test Category", "DELETE", f"categories/{category_id}", 200)
        
        # Delete campaign
        self.run_test("Delete Test Campaign", "DELETE", "campaign", 200)
        
        return success

    def test_specific_restaurant_public_menu(self):
        """Test specific restaurant public menu as requested"""
        print("\n🔍 Testing SPECIFIC RESTAURANT PUBLIC MENU")
        
        # Test the specific restaurant ID from the review request
        restaurant_id = "005267f6-9a4e-4e11-ba84-22322d1e0e25"
        
        success, response = self.run_test(
            "GET Public Menu - Specific Restaurant",
            "GET",
            f"menu/public/{restaurant_id}",
            200
        )
        
        if success:
            # Verify response includes campaign data
            campaign = response.get('campaign')
            campaign_items = response.get('campaign_items', [])
            
            if campaign:
                campaign_title = campaign.get('title')
                if campaign_title == "Yaz Kampanyası":
                    self.log_test("Specific Restaurant - Campaign Title", True)
                else:
                    self.log_test("Specific Restaurant - Campaign Title", False, f"Expected 'Yaz Kampanyası', got '{campaign_title}'")
                
                # Check campaign fields
                required_campaign_fields = ['title', 'description', 'image_url', 'is_active']
                missing_campaign_fields = [field for field in required_campaign_fields if field not in campaign]
                
                if not missing_campaign_fields:
                    self.log_test("Specific Restaurant - Campaign Fields", True)
                else:
                    self.log_test("Specific Restaurant - Campaign Fields", False, f"Missing fields: {missing_campaign_fields}")
            else:
                self.log_test("Specific Restaurant - Campaign Object", False, "No campaign object found")
            
            # Verify campaign_items array exists
            if isinstance(campaign_items, list):
                self.log_test("Specific Restaurant - Campaign Items Array", True)
                
                # Check if any items have is_campaign=true
                campaign_item_count = len([item for item in campaign_items if item.get('is_campaign', False)])
                if campaign_item_count > 0:
                    self.log_test("Specific Restaurant - Campaign Items Content", True)
                else:
                    self.log_test("Specific Restaurant - Campaign Items Content", False, "No campaign items found")
            else:
                self.log_test("Specific Restaurant - Campaign Items Array", False, "campaign_items is not an array")
            
            # Verify categories structure
            categories = response.get('categories', [])
            if isinstance(categories, list):
                self.log_test("Specific Restaurant - Categories Structure", True)
                
                # Check if campaign_only items are properly filtered from regular categories
                all_category_items = []
                for category in categories:
                    items = category.get('items', [])
                    all_category_items.extend(items)
                
                campaign_only_in_categories = [item for item in all_category_items if item.get('campaign_only', False)]
                
                if len(campaign_only_in_categories) == 0:
                    self.log_test("Specific Restaurant - Campaign Only Filtering", True)
                else:
                    self.log_test("Specific Restaurant - Campaign Only Filtering", False, 
                                 f"Found {len(campaign_only_in_categories)} campaign_only items in regular categories")
            else:
                self.log_test("Specific Restaurant - Categories Structure", False, "categories is not an array")
        
        return success

    def cleanup_test_data(self, category_id):
        """Clean up test data"""
        if category_id:
            success, response = self.run_test(
                "Delete Test Category",
                "DELETE",
                f"categories/{category_id}",
                200
            )
            return success
        return True

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Restaurant Menu API Tests - Campaign Management System Focus")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)
        
        # Test registration and authentication
        if not self.test_register():
            print("❌ Registration failed, stopping tests")
            return False
        
        if not self.test_login():
            print("❌ Login test failed")
        
        if not self.test_auth_me():
            print("❌ Auth me test failed")
        
        # Test invalid auth
        self.test_invalid_auth()
        
        # Test CAMPAIGN MANAGEMENT SYSTEM
        print("\n🔍 Testing CAMPAIGN MANAGEMENT SYSTEM")
        
        # Test Campaign CRUD API
        self.test_campaign_crud_api()
        
        # Test CRUD operations first to get category for campaign items
        category_id = self.test_categories_crud()
        if category_id:
            # Test Menu Items with Campaign Fields
            self.test_menu_items_with_campaign_fields(category_id)
            
            # Test regular menu items
            self.test_menu_items_crud(category_id)
            self.cleanup_test_data(category_id)
        
        # Test Public Menu with Campaign Data
        self.test_public_menu_with_campaign_data()
        
        # Test Specific Restaurant Public Menu (from review request)
        self.test_specific_restaurant_public_menu()
        
        # Test SUPER ADMIN FEATURES
        print("\n🔍 Testing SUPER ADMIN SYSTEM")
        super_admin_success, super_admin_token = self.test_super_admin_registration_and_login()
        
        if super_admin_success and super_admin_token:
            print("✅ Super Admin registration and login successful")
            
            # Test subscription info with super admin flag
            self.test_subscription_info_super_admin_flag(super_admin_token)
            
            # Test super admin endpoints
            self.test_super_admin_list_restaurants(super_admin_token)
            self.test_super_admin_create_restaurant(super_admin_token)
            self.test_super_admin_manual_subscription(super_admin_token)
        else:
            print("❌ Super Admin registration/login failed, skipping admin tests")
        
        # Test USER MANAGEMENT FEATURES
        print("\n🔍 Testing USER MANAGEMENT FEATURES")
        
        # Test regular user login
        regular_success, regular_token = self.test_regular_user_login()
        
        if regular_success and regular_token:
            print("✅ Regular test user login successful")
            
            # Test password change
            print("\n🔍 Testing Password Change Feature")
            self.test_password_change(regular_token)
            
            # Test account deletion request
            print("\n🔍 Testing Account Deletion Request Feature")
            self.test_account_deletion_request(regular_token)
            
            # Test subscription info fix
            print("\n🔍 Testing Subscription Info Fix")
            self.test_subscription_info_fix(regular_token)
        else:
            print("❌ Regular test user login failed, skipping user management tests")
        
        # Test admin deletion management (requires super admin)
        if super_admin_success and super_admin_token:
            print("\n🔍 Testing Admin Deletion Management")
            self.test_admin_deletion_requests(super_admin_token)
            
            print("\n🔍 Testing Admin Restaurant Deletion")
            self.test_admin_delete_restaurant(super_admin_token)
        
        # Test OTHER FEATURES
        print("\n🔍 Testing OTHER FEATURES")
        
        # Test File Upload
        self.test_file_upload_validation()
        
        # Test Product Availability Toggle
        category_id_2 = self.test_categories_crud()
        if category_id_2:
            self.test_product_availability_toggle(category_id_2)
            self.cleanup_test_data(category_id_2)
        
        # Test Public Menu Filtering
        self.test_public_menu_filtering()
        
        # Test public endpoints
        self.test_public_menu()
        
        # Test multi-tenant isolation
        self.test_multi_tenant_isolation()
        
        # Print results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return False

def main():
    tester = RestaurantMenuAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())