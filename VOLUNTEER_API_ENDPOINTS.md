# Volunteer API Endpoints - Frontend Reference

Complete list of all volunteer endpoints with request payloads and descriptions.

---

## 1. Volunteer Registration

**Endpoint:** `POST /volunteer/registration`

**Description:** Register a new volunteer account

**Payload:**
```json
{
  "name": "Volunteer Name",
  "email": "volunteer@example.com",
  "password": "password123",
  "contact_number": "1234567890",
  "address": "123 Main St, City, State",
  "lat": "40.7128",
  "lng": "-74.0060",
  "serving_distance": "10",
  "place_id": "optional_place_id",
  "firebase_token": "firebase_token_here",
  "role": "Volunteer"
}
```

**Required Fields:**
- `name`
- `email`
- `password`
- `contact_number`
- `address`
- `lat`
- `lng`
- `serving_distance`
- `firebase_token`
- `role` (should be "Volunteer")

---

## 2. Update Volunteer Profile

**Endpoint:** `POST /volunteer/update_profile`

**Description:** Update volunteer profile information

**Payload:**
```json
{
  "user_id": "volunteer_mongodb_id_here",
  "name": "Updated Name",
  "serving_distance": "15",
  "contact_number": "1234567890",
  "address": "Updated Address",
  "lat": "40.7128",
  "lng": "-74.0060",
  "place_id": "optional_place_id"
}
```

**Required Fields:**
- `user_id`
- `name`
- `serving_distance`
- `contact_number`
- `address`
- `lat`
- `lng`
- `place_id`

---

## 3. Get Available Food List

**Endpoint:** `POST /volunteer/getAvailableFoodList`

**Description:** Get list of available food donations within volunteer's serving distance

**Payload:**
```json
{
  "volunteer_lat": "40.7128",
  "volunteer_lng": "-74.0060",
  "serving_distance": "10"
}
```

**Required Fields:**
- `volunteer_lat`
- `volunteer_lng`
- `serving_distance`

**Returns:** List of available foods with distance calculations

---

## 4. Get Food Item Details

**Endpoint:** `POST /volunteer/getFoodItemDetails`

**Description:** Get detailed donor information for a specific food item

**Payload:**
```json
{
  "donor_user_id": "donor_mongodb_id_here",
  "volunteer_lat": "40.7128",
  "volunteer_lng": "-74.0060"
}
```

**Required Fields:**
- `donor_user_id`

**Optional Fields:**
- `volunteer_lat` (for distance calculation)
- `volunteer_lng` (for distance calculation)

**Returns:** Donor details including name, contact, address, and distance

---

## 5. Collect Food (Accept Food Donation)

**Endpoint:** `POST /volunteer/collect_food`

**Description:** Volunteer accepts/commits to pick up a food donation

**Payload:**
```json
{
  "food_item_id": "food_item_mongodb_id_here",
  "volunteer_user_id": "volunteer_mongodb_id_here"
}
```

**Required Fields:**
- `food_item_id`
- `volunteer_user_id`

**Status Transition:** `Available` → `Pick up scheduled`

**Note:** No recipient_id needed at this stage. Volunteer chooses recipient later when delivering.

---

## 6. Mark Picked Up

**Endpoint:** `POST /volunteer/mark_picked_up`

**Description:** Volunteer marks food as physically collected from donor location

**Payload:**
```json
{
  "food_item_id": "food_item_mongodb_id_here",
  "volunteer_user_id": "volunteer_mongodb_id_here"
}
```

**Required Fields:**
- `food_item_id`
- `volunteer_user_id` ⭐ (Validates that only the volunteer who collected the food can mark it as picked up)

**Status Transition:** `Pick up scheduled` → `Collected food`

**Note:** Records `picked_up_at` timestamp automatically. Validates that the volunteer making the request is the same one who collected the food.

---

## 7. Mark Delivered

**Endpoint:** `POST /volunteer/mark_delivered`

**Description:** Volunteer marks food as delivered to recipient/shelter

**Payload:**
```json
{
  "food_item_id": "food_item_mongodb_id_here",
  "volunteer_user_id": "volunteer_mongodb_id_here",
  "recipient_id": "recipient_mongodb_id_here"
}
```

**Required Fields:**
- `food_item_id`
- `volunteer_user_id` ⭐ (Validates that only the volunteer who collected the food can mark it as delivered)
- `recipient_id` ⭐ (Required - volunteer selects recipient when delivering)

**Status Transition:** `Collected food` → `Delivered`

**Note:** Records `delivered_at` timestamp automatically. Validates that the volunteer making the request is the same one who collected the food.

---

## 8. Get All Foods by Volunteer

**Endpoint:** `POST /volunteer/getAllFoodsByVolunteer`

**Description:** Get all foods that volunteer has collected (regardless of status)

**Payload:**
```json
{
  "user_id": "volunteer_mongodb_id_here"
}
```

**Required Fields:**
- `user_id`

**Returns:** List of all foods collected by volunteer (with status: Pick up scheduled, Collected food, or Delivered)

---

## 9. Get Recipients List

**Endpoint:** `GET /admin/get_all_recipients` or `POST /admin/get_all_recipients`

**Description:** Get list of recipients, optionally filtered by 10 miles radius of volunteer location

**Payload (POST):**
```json
{
  "volunteer_id": "volunteer_mongodb_id_here"
}
```

**Query Parameters (GET):**
- `volunteer_id` (optional) - If provided, filters recipients within 10 miles radius

**Optional Fields:**
- `volunteer_id` - If provided, filters recipients within 10 miles radius. If not provided, returns all recipients.

**Returns:** 
- If `volunteer_id` provided: List of recipients within 10 miles, sorted by distance (closest first), with `distance` field in miles
- If `volunteer_id` not provided: List of all recipients

**Example Response:**
```json
{
  "message": "Success",
  "error": false,
  "data": {
    "total_count": 3,
    "recipients": [
      {
        "user_id": "507f1f77bcf86cd799439011",
        "name": "Recipient Name",
        "address": "123 Main St",
        "lat": "40.7128",
        "lng": "-74.0060",
        "distance": 2.5,
        "role": "Recipient"
      }
    ]
  }
}
```

---

## Complete Workflow Example

### Step 1: Volunteer accepts food
```
POST /volunteer/collect_food
{
  "food_item_id": "507f1f77bcf86cd799439011",
  "volunteer_user_id": "507f1f77bcf86cd799439012"
}
```

### Step 2: Volunteer picks up food
```
POST /volunteer/mark_picked_up
{
  "food_item_id": "507f1f77bcf86cd799439011",
  "volunteer_user_id": "507f1f77bcf86cd799439012"
}
```

### Step 3: Volunteer delivers food (with recipient selection)
```
POST /volunteer/mark_delivered
{
  "food_item_id": "507f1f77bcf86cd799439011",
  "volunteer_user_id": "507f1f77bcf86cd799439012",
  "recipient_id": "507f1f77bcf86cd799439013"
}
```

---

## Status Flow Summary

```
📦 Available
    ↓ (collect_food)
📅 Pick up scheduled
    ↓ (mark_picked_up)
📦 Collected food
    ↓ (mark_delivered + recipient_id)
✅ Delivered
```

---

## Important Notes

1. **Recipient Selection**: `recipient_id` is only required when marking as delivered (`mark_delivered`), not when accepting or collecting food.

2. **Distance Calculation**: Use `volunteer_lat` and `volunteer_lng` for accurate distance calculations in available food lists.

3. **Status Validation**: Each endpoint validates the current food status before allowing transitions. Make sure to handle error responses appropriately.

4. **Notifications**: Donors receive email notifications when:
   - Volunteer accepts food (collect_food)
   - Volunteer picks up food (mark_picked_up)
   - Volunteer delivers food (mark_delivered)

