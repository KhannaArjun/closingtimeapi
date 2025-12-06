# Volunteer Food Collection/Drop Status Workflow

## Status Definitions (4-Status Flow)

All status constants are defined in `utils/constants.py`:

| Status | Constant | Description |
|--------|----------|-------------|
| **Available** | `constants.Utils.available` | Initial status when food donation is first created. Food is available for volunteers to accept. |
| **Pick up scheduled** | `constants.Utils.pickeup_schedule` | Volunteer has accepted/committed to pick up this food. Donor is notified. Food is scheduled for pickup. |
| **Collected food** | `constants.Utils.collected` | Volunteer has physically collected food from donor location. Food is now with volunteer, on the way to recipient. |
| **Delivered** | `constants.Utils.delivered` | Food successfully delivered to recipient/shelter. Final status. |
| **Expired** | `constants.Utils.expired` | Defined but currently not actively used |
| **Already assigned** | `constants.Utils.already_assigned` | Error message when food is already assigned to another volunteer |

### Deprecated Statuses (Backward Compatibility)

| Status | Constant | Replacement |
|--------|----------|-------------|
| **Waiting for pickup** | `constants.Utils.waiting_for_volunteer` | Use `available` instead |

---

## Status Flow Diagram

```
📦 Food Donation Created
         ↓
    [Available]
         ↓
🚴 Volunteer accepts food
    (POST /volunteer/collect_food)
         ↓
    [Pick up scheduled]
         ↓
🚴 Volunteer physically picks up food
    (POST /volunteer/mark_picked_up)
         ↓
    [Collected food]
         ↓
🚴 Volunteer delivers to recipient
    (POST /volunteer/mark_delivered)
         ↓
    [Delivered]
```

---

## Status Transitions & Endpoints

### 1. **Available** → **Pick up scheduled**

**Endpoint:** `POST /volunteer/collect_food`

**Trigger:** When a volunteer accepts/commits to pick up a food donation

**Code Location:** `app.py:1417-1441`

**Requirements:**
- Food status must be `Available` (or deprecated `waiting_for_volunteer` for backward compatibility)
- If food is already in `Pick up scheduled` status, returns error: "Already assigned to another Rider"

```python
if add_food_obj['status'] in [constants.Utils.available, constants.Utils.waiting_for_volunteer]:
    collect_food_col.insert_one(input).inserted_id
    add_food_col.update_one({'_id': ObjectId(input['food_item_id'])}, {
        '$set': {'status': constants.Utils.pickeup_schedule}  # "Pick up scheduled"
    })
```

**Actions:**
- Creates a record in `collect_food` collection
- Updates food status to "Pick up scheduled"
- Sends email notification to donor that volunteer has accepted pickup
- Food is no longer available for other volunteers

---

### 2. **Pick up scheduled** → **Collected food**

**Endpoint:** `POST /volunteer/mark_picked_up`

**Trigger:** When volunteer physically collects food from donor location

**Code Location:** `app.py:1472-1520`

**Requirements:**
- Food status must be `Pick up scheduled` (or deprecated `waiting_for_volunteer` for backward compatibility)
- Returns error if food is not in correct status

```python
if add_food_obj['status'] not in [constants.Utils.pickeup_schedule, constants.Utils.waiting_for_volunteer]:
    return error_response("Food must be in 'Pick up scheduled' status before marking as collected")

add_food_col.update_one({
    '_id': ObjectId(input['food_item_id'])
}, {
    '$set': {
        'status': constants.Utils.collected,  # "Collected food"
        'picked_up_at': datetime.now().isoformat()
    }
})
```

**Actions:**
- Updates status to "Collected food"
- Records `picked_up_at` timestamp
- Sends email notification to donor that food has been collected

---

### 3. **Collected food** → **Delivered**

**Endpoint:** `POST /volunteer/mark_delivered`

**Trigger:** When volunteer delivers food to recipient/shelter

**Code Location:** `app.py:1523-1570`

**Requirements:**
- Food status must be `Collected food` (or `Pick up scheduled` for backward compatibility)
- Returns error if food is not in correct status

```python
if add_food_obj['status'] not in [constants.Utils.collected, constants.Utils.pickeup_schedule]:
    return error_response("Food must be in 'Collected food' status before marking as delivered")

add_food_col.update_one({
    '_id': ObjectId(input['food_item_id'])
}, {
    '$set': {
        'status': constants.Utils.delivered,  # "Delivered"
        'delivered_at': datetime.now().isoformat()
    }
})
```

**Actions:**
- Updates status to "Delivered"
- Records `delivered_at` timestamp
- Sends email notification to donor that food has been delivered

---

## Initial Status Setting

### When Food is First Created

**Regular Donation:** `POST /food_donor/add_food`
- No explicit status set (should default to `Available` in frontend/database)

**QR Code Donation:** `POST /qr_donate_food`
- Explicitly sets initial status to `Available`

**Code Location:** `app.py:2415`

```python
food_donation = {
    # ... other fields ...
    'status': constants.Utils.available,  # "Available"
    # ...
}
```

---

## Food Item Status Queries

### Available Food List for Volunteers

**Endpoint:** `POST /volunteer/getAvailableFoodList`

**Code Location:** `app.py:1337-1365`

Shows foods that are available for volunteers to accept:
- `Available`
- `waiting_for_volunteer` (deprecated, for backward compatibility)
- `pickeup_schedule` (Pick up scheduled - still shown in available list)

**Note:** Foods in `Delivered` status are NOT shown. Foods in `Pick up scheduled` status are still shown in the available list.

```python
"status": {"$in": [
    constants.Utils.available,
    constants.Utils.waiting_for_volunteer,  # Deprecated
    constants.Utils.pickeup_schedule  # Pick up scheduled
]}
```

### All Foods by Volunteer

**Endpoint:** `POST /volunteer/getAllFoodsByVolunteer`

**Code Location:** `app.py:1549-1582`

Returns all foods that a volunteer has collected (regardless of status), filtered by:
- Foods where volunteer has a record in `collect_food` collection
- Foods with `pick_up_date >= present_date` (not expired)

---

## Error Handling

### Already Assigned Error

**Constant:** `constants.Utils.already_assigned`
**Value:** `"Already assigned to another Rider"`

**Triggered when:**
- Volunteer tries to collect food that's not in `Available` or `waiting_for_volunteer` status

**Code Location:** `app.py:1438-1439`

```python
if add_food_obj['status'] not in [constants.Utils.available, constants.Utils.waiting_for_volunteer]:
    return flask.jsonify(api_response.apiResponse(constants.Utils.already_assigned, False, {}))
```

### Invalid Status Transition Errors

**Mark Picked Up:**
- Error: "Food must be in 'Pick up scheduled' status before marking as collected"
- Triggered when trying to mark as collected from wrong status

**Mark Delivered:**
- Error: "Food must be in 'Collected food' status before marking as delivered"
- Triggered when trying to mark as delivered from wrong status

---

## Workflow Summary

1. **Donor donates food** → Status: `Available`
   - Volunteers nearby are notified via push notifications and email

2. **Volunteer accepts** → Status: `Pick up scheduled`
   - Volunteer commits to pick up
   - **Donor receives email notification** that volunteer has accepted pickup
   - Food status updated to "Pick up scheduled"
   - Note: Food may still appear in available list (implementation shows `pickeup_schedule` in available foods)

3. **Volunteer picks up** → Status: `Collected food`
   - Volunteer physically collects food from donor
   - `picked_up_at` timestamp recorded
   - **Donor receives email notification** that food has been collected
   - Food is now with volunteer, on the way to recipient

4. **Volunteer delivers** → Status: `Delivered`
   - Food delivered to recipient/shelter
   - `delivered_at` timestamp recorded
   - **Donor receives email notification** that food has been delivered
   - Workflow complete

---

## Notes

1. **Backward Compatibility**: Deprecated status (`waiting_for_volunteer`) is still accepted in validation checks to support existing data
2. **Status Validation**: Each endpoint validates the current status before allowing transitions
3. **Notifications**: 
   - **Donors**: Receive **email notifications** (not push notifications, as donors don't use the app) when volunteer accepts food, when food is collected, and when food is delivered
   - **Volunteers**: Receive Firebase push notifications and email notifications
4. **Timestamps**: Both `picked_up_at` and `delivered_at` are automatically recorded when status changes
5. **No Recipient Acceptance**: Recipients do not actively accept food in this workflow - volunteers directly collect and deliver
6. **Available List Behavior**: Foods with status `pickeup_schedule` are still shown in the available food list for volunteers

---

## API Endpoints Summary

| Endpoint | Method | Status Transition | Description |
|----------|--------|-------------------|-------------|
| `/volunteer/collect_food` | POST | `Available` → `Pick up scheduled` | Volunteer accepts food donation |
| `/volunteer/mark_picked_up` | POST | `Pick up scheduled` → `Collected food` | Volunteer physically collects food from donor |
| `/volunteer/mark_delivered` | POST | `Collected food` → `Delivered` | Volunteer delivers food to recipient |
| `/volunteer/getAvailableFoodList` | POST | - | Get list of available foods for volunteers (includes `available`, `waiting_for_volunteer`, and `pickeup_schedule`) |
| `/volunteer/getAllFoodsByVolunteer` | POST | - | Get all foods collected by a volunteer |
