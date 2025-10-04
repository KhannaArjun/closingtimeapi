class Utils:

    success = "Success"
    failed = "failed"
    user_exists = "User already exists"
    contact_number_exists = "Contact number already exists"
    invalid_cred = "Invalid credentials"
    inserted = "Inserted"
    new_user = "new user"
    deleted = "deleted"
    updated = "updated"
    no_user_found = "No user profile found"
    fb_food_added_topic = "food_added"
    recipient = "Recipient"
    volunteer = "Volunteer"
    donor = "Donor"
    expired = "Expired"
    waiting_for_volunteer = "Waiting for pickup"
    pickeup_schedule = "Pick up scheduled"
    delivered = "Delivered"
    already_assigned = "Already assigned to another Rider"
    miles = 10
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "sclosingtime@gmail.com"
    smtp_password = "whmsuoiaozvfyaxp"  # Replace with your Gmail App Password
    available = "Available"
    qr_business_collection = "qr_business_registration"
    # Server URL for QR codes - use your laptop's IP for testing from phone
    server_url = "http://192.168.0.30:5005"  # Change to your server's public IP/domain in production
    # QR token expiration time in hours
    qr_token_expiry_hours = 2

# def parse():
#     json = [
#         {
#             "name": "Alabama",
#             "abbreviation": "AL"
#         },
#         {
#             "name": "Alaska",
#             "abbreviation": "AK"
#         },
#         {
#             "name": "American Samoa",
#             "abbreviation": "AS"
#         },
#         {
#             "name": "Arizona",
#             "abbreviation": "AZ"
#         },
#         {
#             "name": "Arkansas",
#             "abbreviation": "AR"
#         },
#         {
#             "name": "California",
#             "abbreviation": "CA"
#         },
#         {
#             "name": "Colorado",
#             "abbreviation": "CO"
#         },
#         {
#             "name": "Connecticut",
#             "abbreviation": "CT"
#         },
#         {
#             "name": "Delaware",
#             "abbreviation": "DE"
#         },
#         {
#             "name": "District Of Columbia",
#             "abbreviation": "DC"
#         },
#         {
#             "name": "Federated States Of Micronesia",
#             "abbreviation": "FM"
#         },
#         {
#             "name": "Florida",
#             "abbreviation": "FL"
#         },
#         {
#             "name": "Georgia",
#             "abbreviation": "GA"
#         },
#         {
#             "name": "Guam",
#             "abbreviation": "GU"
#         },
#         {
#             "name": "Hawaii",
#             "abbreviation": "HI"
#         },
#         {
#             "name": "Idaho",
#             "abbreviation": "ID"
#         },
#         {
#             "name": "Illinois",
#             "abbreviation": "IL"
#         },
#         {
#             "name": "Indiana",
#             "abbreviation": "IN"
#         },
#         {
#             "name": "Iowa",
#             "abbreviation": "IA"
#         },
#         {
#             "name": "Kansas",
#             "abbreviation": "KS"
#         },
#         {
#             "name": "Kentucky",
#             "abbreviation": "KY"
#         },
#         {
#             "name": "Louisiana",
#             "abbreviation": "LA"
#         },
#         {
#             "name": "Maine",
#             "abbreviation": "ME"
#         },
#         {
#             "name": "Marshall Islands",
#             "abbreviation": "MH"
#         },
#         {
#             "name": "Maryland",
#             "abbreviation": "MD"
#         },
#         {
#             "name": "Massachusetts",
#             "abbreviation": "MA"
#         },
#         {
#             "name": "Michigan",
#             "abbreviation": "MI"
#         },
#         {
#             "name": "Minnesota",
#             "abbreviation": "MN"
#         },
#         {
#             "name": "Mississippi",
#             "abbreviation": "MS"
#         },
#         {
#             "name": "Missouri",
#             "abbreviation": "MO"
#         },
#         {
#             "name": "Montana",
#             "abbreviation": "MT"
#         },
#         {
#             "name": "Nebraska",
#             "abbreviation": "NE"
#         },
#         {
#             "name": "Nevada",
#             "abbreviation": "NV"
#         },
#         {
#             "name": "New Hampshire",
#             "abbreviation": "NH"
#         },
#         {
#             "name": "New Jersey",
#             "abbreviation": "NJ"
#         },
#         {
#             "name": "New Mexico",
#             "abbreviation": "NM"
#         },
#         {
#             "name": "New York",
#             "abbreviation": "NY"
#         },
#         {
#             "name": "North Carolina",
#             "abbreviation": "NC"
#         },
#         {
#             "name": "North Dakota",
#             "abbreviation": "ND"
#         },
#         {
#             "name": "Northern Mariana Islands",
#             "abbreviation": "MP"
#         },
#         {
#             "name": "Ohio",
#             "abbreviation": "OH"
#         },
#         {
#             "name": "Oklahoma",
#             "abbreviation": "OK"
#         },
#         {
#             "name": "Oregon",
#             "abbreviation": "OR"
#         },
#         {
#             "name": "Palau",
#             "abbreviation": "PW"
#         },
#         {
#             "name": "Pennsylvania",
#             "abbreviation": "PA"
#         },
#         {
#             "name": "Puerto Rico",
#             "abbreviation": "PR"
#         },
#         {
#             "name": "Rhode Island",
#             "abbreviation": "RI"
#         },
#         {
#             "name": "South Carolina",
#             "abbreviation": "SC"
#         },
#         {
#             "name": "South Dakota",
#             "abbreviation": "SD"
#         },
#         {
#             "name": "Tennessee",
#             "abbreviation": "TN"
#         },
#         {
#             "name": "Texas",
#             "abbreviation": "TX"
#         },
#         {
#             "name": "Utah",
#             "abbreviation": "UT"
#         },
#         {
#             "name": "Vermont",
#             "abbreviation": "VT"
#         },
#         {
#             "name": "Virgin Islands",
#             "abbreviation": "VI"
#         },
#         {
#             "name": "Virginia",
#             "abbreviation": "VA"
#         },
#         {
#             "name": "Washington",
#             "abbreviation": "WA"
#         },
#         {
#             "name": "West Virginia",
#             "abbreviation": "WV"
#         },
#         {
#             "name": "Wisconsin",
#             "abbreviation": "WI"
#         },
#         {
#             "name": "Wyoming",
#             "abbreviation": "WY"
#         }
#     ]
#
#     for x in json:
#         print(str(x['name']) + str(","))