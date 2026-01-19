# TODO: Fix Custom Order Constructor Step 6 Bug

## Issue
On step 6 of the individual order constructor, the system doesn't allow adding the product to the cart and doesn't transition to the cart page.

## Root Cause
The JavaScript fetch request to finalize the custom order fails when the user's session has expired. The Django view redirects to the login page (HTTP 302), but the fetch doesn't follow redirects by default, causing the response to be HTML instead of JSON, leading to a parsing error.

## Solution
Modified the JavaScript in `templates/custom_orders/constructor_summary.html` to properly handle redirect responses from the server. Added checks for HTTP status 302 and 401 to redirect the user to the login page.

## Changes Made
- Updated `finalizeOrder()` function in `constructor_summary.html`
- Added response status checks before attempting to parse JSON
- If status is 302 or 401, redirect to login page
- Improved error handling for other HTTP errors

## Testing Performed
### Code Review
- Verified Django settings and URL configurations are correct
- Checked that CSRF token is properly included in base.html
- Confirmed the finalize_custom_order view handles authentication correctly
- Validated JavaScript syntax and logic flow

### Test Cases (To be executed manually)
1. **Authenticated User - Successful Add to Cart**
   - Login as user
   - Navigate through constructor steps 1-6
   - Click "Добавить в корзину" on step 6
   - Expected: Success alert, redirect to /cart/, item appears in cart

2. **Unauthenticated User - Redirect to Login**
   - Clear session or use incognito
   - Attempt to access step 6
   - Click "Добавить в корзину"
   - Expected: Redirect to login page with next parameter

3. **Session Expired During Process**
   - Login, start constructor
   - Wait for session to expire or manually expire session
   - Click "Добавить в корзину"
   - Expected: Redirect to login page

4. **Server Error Handling**
   - Simulate server errors (invalid data, etc.)
   - Expected: Appropriate error messages displayed

5. **Cart Page Verification**
   - After successful add, verify cart shows custom item with correct price
   - Verify cart total calculation includes custom pricing

## Status
Code changes implemented. Manual testing required to verify functionality.
