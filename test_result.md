# Test Results - Logistics OS

## Current Test Session: Session Stability & Unified Tracking System

### Test Objectives
1. Verify session persistence (30-day token)
2. Verify profile dropdown menu functionality  
3. Test Unified Tracking System with Time Travel for ZR Express Mock

### Backend Endpoints to Test
- POST /api/auth/login - Should return access_token stored in localStorage
- GET /api/orders - Should return orders with carrier_type and carrier_tracking_id fields
- POST /api/shipping/sync-status/{order_id} - Should advance ZR Express mock status (Time Travel)
- GET /api/shipping/timeline/{order_id} - Should return timeline data for visual display

### Frontend Components to Test
1. Profile dropdown menu should open on click (top-right header)
2. Orders page should display carrier info (carrier_type, carrier_tracking_id)
3. Tracking dialog should show:
   - Visual timeline with progress steps
   - "Actualiser" button for sync
   - ZR Express "Mode Démo" notice

### Test Credentials
- Admin: cherier.sam@beyondexpress-batna.com / admin123456
- Test Order with ZR Express: BEX-D07A89F3025E (ID: 8c1b0c8a-7a6d-441a-b168-a06e1c74e90e)

### Incorporate User Feedback
- Session should persist without 401 errors during navigation
- Profile menu must open on first click
- Time Travel should work: clicking "Actualiser" advances status (pending->in_transit->delivered)
