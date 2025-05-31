import requests
import base64
from typing import Optional, Dict, Any, List

from src.app.core.config import settings

class IgaClient:
    """
    Client for interacting with an Identity Governance and Administration (IGA) system.
    This initial version is geared towards midPoint's conceptual API structure,
    but can be adapted or subclassed for other IGA tools like Syncope.
    """

    def __init__(self, base_url: Optional[str] = None, api_key_or_creds: Optional[str] = None):
        self.base_url = base_url or settings.IGA_API_URL
        self.api_key_or_creds = api_key_or_creds or settings.IGA_API_KEY

        if not self.base_url:
            raise ValueError("IGA_API_URL (or base_url) must be configured.")

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json", # Prefer JSON responses
        }
        self._setup_auth()

    def _setup_auth(self):
        """Sets up authentication headers based on api_key_or_creds."""
        if self.api_key_or_creds:
            if ":" in self.api_key_or_creds: # Basic Auth: "username:password"
                username, password = self.api_key_or_creds.split(":", 1)
                auth_string = f"{username}:{password}"
                encoded_auth_string = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
                self.headers["Authorization"] = f"Basic {encoded_auth_string}"
            else: # Token-based Auth (e.g., Bearer token or simple API key)
                # Assuming it's a Bearer token by default for simplicity.
                # If it's a custom API key header, this needs adjustment or a different setting.
                self.headers["Authorization"] = f"Bearer {self.api_key_or_creds}"
        # If no api_key_or_creds, no Authorization header is set (public access or other auth method)

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Helper method to make HTTP requests."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
            return response
        except requests.exceptions.RequestException as e:
            # Log the error e
            print(f"IGA Client Request Error: {e}") # Replace with actual logging
            # Consider raising a custom exception
            raise

    # --- Domain/Organization Management (Conceptual) ---
    # These methods are highly dependent on the specific IGA tool.
    # The examples below are generic placeholders.

    def create_organization(self, org_name: str, org_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Conceptually creates an organization (e.g., for a new tenant in midPoint).
        Endpoint and payload are placeholders.
        """
        # Assuming midPoint-like endpoint for orgs
        endpoint = "orgs"
        payload = {"name": org_name}
        if org_details:
            payload.update(org_details)

        # midPoint might expect XML by default for some operations or specific Content-Type
        # For this example, sticking to JSON and assuming midPoint is configured for it or has JSON endpoints.
        # If XML is needed: self.headers["Content-Type"] = "application/xml", and format payload as XML.

        response = self._request("POST", endpoint, json=payload)
        return response.json()

    def delete_organization(self, org_identifier: str) -> bool:
        """
        Conceptually deletes an organization.
        org_identifier could be OID for midPoint or key for Syncope.
        """
        endpoint = f"orgs/{org_identifier}"
        try:
            self._request("DELETE", endpoint)
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False # Or handle as "already deleted"
            raise # Re-raise other HTTP errors

    # --- User Management (Conceptual) ---

    def create_user(self, user_data: Dict[str, Any], tenant_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a user in the IGA system.
        'tenant_context' might be an org OID for midPoint, or a domain name for Syncope (passed in headers).
        Payload structure is highly IGA-specific.
        """
        endpoint = "users"
        headers_override = self.headers.copy()

        if tenant_context:
            # Example for Syncope: Domain passed in header
            # headers_override["X-Syncope-Domain"] = tenant_context
            # For midPoint, tenant_context (org OID) would be part of user_data payload (e.g., parentOrgRef)
            if "parentOrgRef" not in user_data and not any(ref.get("type") == "OrgType" for ref in user_data.get("parentOrgRefs", [])):
                 # This is a simplistic check. midPoint user creation often involves linking to an org.
                 # user_data.setdefault("parentOrgRef", [{"oid": tenant_context, "type": "OrgType"}])
                 pass # Assume org linkage is handled in user_data construction by caller for now

        response = self._request("POST", endpoint, json=user_data, headers=headers_override)
        return response.json()

    def get_user(self, user_identifier: str, tenant_context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves a user by a unique identifier (e.g., username, OID).
        """
        endpoint = f"users/{user_identifier}" # This might need adjustment (e.g., /users?filter=...)
        headers_override = self.headers.copy()
        # Add tenant context header if needed (e.g., for Syncope)
        # if tenant_context: headers_override["X-Syncope-Domain"] = tenant_context
        try:
            response = self._request("GET", endpoint, headers=headers_override)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def delete_user(self, user_identifier: str, tenant_context: Optional[str] = None) -> bool:
        """
        Deletes a user by a unique identifier.
        """
        endpoint = f"users/{user_identifier}"
        headers_override = self.headers.copy()
        # Add tenant context header if needed
        # if tenant_context: headers_override["X-Syncope-Domain"] = tenant_context
        try:
            self._request("DELETE", endpoint, headers=headers_override)
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False # Or handle as "already deleted"
            raise

    def assign_role_to_user(
        self, user_identifier: str, role_identifier: str, tenant_context: Optional[str] = None
    ) -> bool:
        """
        Assigns a role to a user. This is highly IGA-specific.
        Often involves modifying the user resource (e.g., adding to 'assignment' in midPoint).
        'role_identifier' could be role OID or name.
        """
        # Example for midPoint: PATCH user with new assignment
        # endpoint = f"users/{user_identifier}"
        # patch_payload = [
        #     {
        #         "op": "add",
        #         "path": "/assignment",
        #         "value": [{"targetRef": {"oid": role_identifier, "type": "RoleType"}}]
        #     }
        # ]
        # self._request("PATCH", endpoint, json=patch_payload) # Assuming JSON Patch
        print(f"CONCEPTUAL: Assign role '{role_identifier}' to user '{user_identifier}' in context '{tenant_context}'")
        # This method needs concrete implementation based on chosen IGA's specific API for role assignment.
        return True # Placeholder

    def revoke_role_from_user(
        self, user_identifier: str, role_identifier: str, tenant_context: Optional[str] = None
    ) -> bool:
        """
        Revokes a role from a user. Highly IGA-specific.
        """
        print(f"CONCEPTUAL: Revoke role '{role_identifier}' from user '{user_identifier}' in context '{tenant_context}'")
        # Needs concrete implementation.
        return True # Placeholder

    def get_users_and_roles_for_tenant(self, tenant_context: str) -> List[Dict[str, Any]]:
        """
        Conceptual: Fetches users and their roles for a given tenant context.
        This would likely involve multiple API calls or a complex query to the IGA.
        """
        print(f"CONCEPTUAL: Get users and roles for tenant context '{tenant_context}'")
        # Needs concrete implementation.
        return [{"user": "sample_user", "roles": ["sample_role"]}] # Placeholder

# Example Usage (for testing the client if run directly)
# if __name__ == "__main__":
#     # Ensure IGA_API_URL and IGA_API_KEY (e.g., "administrator:5ecr3t") are in .env
#     # or pass them directly:
#     # client = IgaClient(base_url="http://localhost:8080/midpoint/ws/rest", api_key_or_creds="administrator:5ecr3t")
#     client = IgaClient()
#     print(f"IGA Client initialized for URL: {client.base_url}")
#     print(f"IGA Client Auth Headers: {client.headers.get('Authorization')}")
#
#     # Conceptual test - these will likely fail without a running & configured midPoint
#     try:
#         # print("
Attempting to list users (first 5):")
#         # users_response = client._request("GET", "users?pageSize=5") # Example of direct _request usage
#         # print(users_response.json())
#
#         # print("
Attempting to get a specific user (e.g., administrator):")
#         # admin_user_oid = "00000000-0000-0000-0000-000000000002" # Default OID for administrator in midPoint
#         # admin_user = client.get_user(admin_user_oid)
#         # if admin_user:
#         #     print(admin_user)
#         # else:
#         #     print("Administrator user not found or error.")
#
#         # print("
Attempting to create an organization (conceptual):")
#         # new_org = client.create_organization("TestClientOrg")
#         # print(new_org)
#         # if new_org.get("oid"):
#         #    client.delete_organization(new_org["oid"])
#         #    print(f"Org {new_org.get('oid')} deleted conceptually.")

#     except Exception as e:
#         print(f"Error during IGA client test: {e}")
