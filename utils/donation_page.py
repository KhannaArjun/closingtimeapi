def get_donor_registration_email_template(business_name, business_id):

    return f"""
            <html>
            <body>
                <h2>Welcome to Closing Time!</h2>
                <p>Dear {business_name},</p>
                <p>Your business has been successfully registered.</p>
                <p><strong>Business ID:</strong> {business_id}</p>
                <p>Please find your unique QR code attached. Print it and keep it handy.</p>
                
                <h3>How it works:</h3>
                <ol>
                    <li>Staff scans the QR code</li>
                    <li>Takes a photo of surplus food</li>
                    <li>Volunteers pick up and deliver to shelters</li>
                </ol>
                
                <p>Thank you for helping reduce food waste!</p>
                <p>Best regards,<br>Closing Time Team</p>
            </body>
            </html>
            """

def get_food_donate_template(business_data, token):

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Donate Food - {business_data['business_name']}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: linear-gradient(135deg, #ff9500 0%, #ff7b00 100%); 
                min-height: 100vh; 
                padding: 20px; 
            }}
            .container {{ 
                max-width: 500px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
                overflow: hidden; 
            }}
            .logo-container {{ 
                background: #ff9500; 
                padding: 20px; 
                text-align: center; 
                border-bottom: 3px solid #e8850e; 
            }}
            .logo {{ 
                font-size: 32px; 
                font-weight: 700; 
                color: white; 
                text-shadow: 0 2px 4px rgba(0,0,0,0.2); 
            }}
            .header {{ 
                background: linear-gradient(135deg, #ff9500, #e8850e); 
                color: white; 
                padding: 25px 20px; 
                text-align: center; 
            }}
            .header h1 {{ 
                font-size: 24px; 
                margin-bottom: 8px; 
                font-weight: 600; 
            }}
            .header p {{ 
                opacity: 0.95; 
                font-size: 14px; 
                font-weight: 400; 
            }}
            .form-container {{ 
                padding: 30px 20px; 
            }}
            .business-info {{ 
                background: #fff8f0; 
                border: 2px solid #ff9500; 
                border-radius: 12px; 
                padding: 18px; 
                margin-bottom: 25px; 
            }}
            .business-info h3 {{ 
                color: #cc7a00; 
                margin-bottom: 12px; 
                font-size: 16px; 
                font-weight: 600; 
            }}
            .business-info p {{ 
                color: #cc7a00; 
                font-size: 14px; 
                margin-bottom: 6px; 
                font-weight: 500; 
            }}
            .form-group {{ 
                margin-bottom: 22px; 
            }}
            .form-group label {{ 
                display: block; 
                margin-bottom: 10px; 
                font-weight: 600; 
                color: #333; 
                font-size: 15px; 
            }}
            .form-group input, .form-group textarea {{ 
                width: 100%; 
                padding: 14px 16px; 
                border: 2px solid #e1e8ed; 
                border-radius: 12px; 
                font-size: 16px; 
                font-family: inherit; 
                font-weight: 400; 
                transition: all 0.3s ease; 
                background: #fafafa; 
            }}
            .form-group input:focus, .form-group textarea:focus {{ 
                outline: none; 
                border-color: #ff9500; 
                background: white; 
                box-shadow: 0 0 0 3px rgba(255, 149, 0, 0.1); 
            }}
            .form-group textarea {{ 
                resize: vertical; 
                min-height: 90px; 
            }}
            .camera-container {{ 
                margin-bottom: 25px; 
            }}
            #camera-preview {{ 
                width: 100%; 
                height: 250px; 
                background: #f8f9fa; 
                border: 2px dashed #dee2e6; 
                border-radius: 12px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: #6c757d; 
                font-size: 14px; 
                font-weight: 500; 
                overflow: hidden; 
            }}
            #camera-preview img {{ 
                width: 100%; 
                height: 100%; 
                object-fit: cover; 
            }}
            .camera-controls {{ 
                display: flex; 
                gap: 12px; 
                margin-top: 12px; 
            }}
            .btn {{ 
                flex: 1; 
                padding: 14px 20px; 
                border: none; 
                border-radius: 12px; 
                font-size: 16px; 
                font-weight: 600; 
                cursor: pointer; 
                transition: all 0.3s ease; 
                font-family: inherit; 
            }}
            .btn-primary {{ 
                background: #ff9500; 
                color: white; 
            }}
            .btn-primary:hover {{ 
                background: #e8850e; 
                transform: translateY(-2px); 
                box-shadow: 0 6px 20px rgba(255, 149, 0, 0.3); 
            }}
            .btn-secondary {{ 
                background: #6c757d; 
                color: white; 
            }}
            .btn-secondary:hover {{ 
                background: #5a6268; 
                transform: translateY(-1px); 
            }}
            .btn-success {{ 
                background: #ff9500; 
                color: white; 
                width: 100%; 
                margin-top: 25px; 
                padding: 16px 24px; 
                font-size: 17px; 
            }}
            .btn-success:hover {{ 
                background: #e8850e; 
                transform: translateY(-2px); 
                box-shadow: 0 6px 20px rgba(255, 149, 0, 0.3); 
            }}
            .btn-success:disabled {{ 
                background: #ccc; 
                cursor: not-allowed; 
                transform: none; 
                box-shadow: none; 
            }}
            #file-input {{ 
                display: none; 
            }}
            .error {{ 
                background: #f8d7da; 
                color: #721c24; 
                padding: 12px 16px; 
                border-radius: 10px; 
                margin-bottom: 18px; 
                display: none; 
                font-weight: 500; 
            }}
            .error.show {{ 
                display: block; 
            }}
            .success {{ 
                background: #d4edda; 
                color: #155724; 
                padding: 12px 16px; 
                border-radius: 10px; 
                margin-bottom: 18px; 
                display: none; 
                font-weight: 500; 
            }}
            .success.show {{ 
                display: block; 
            }}
            .loading {{ 
                display: none; 
                text-align: center; 
                padding: 25px; 
            }}
            .loading.show {{ 
                display: block; 
            }}
            .spinner {{ 
                border: 4px solid #f3f3f3; 
                border-top: 4px solid #ff9500; 
                border-radius: 50%; 
                width: 45px; 
                height: 45px; 
                animation: spin 1s linear infinite; 
                margin: 0 auto 18px; 
            }}
            @keyframes spin {{ 
                0% {{ transform: rotate(0deg); }} 
                100% {{ transform: rotate(360deg); }} 
            }}
            .required {{ 
                color: #dc3545; 
                font-weight: 700; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo-container">
                <div class="logo">Closing Time</div>
            </div>
            
            <div class="header">
                <h1>Donate Food</h1>
                <p>Help reduce food waste in your community</p>
            </div>

            <div class="form-container">
                <div id="error-message" class="error"></div>
                <div id="success-message" class="success"></div>

                <div class="business-info">
                    <h3>🏢 Business Location</h3>
                    <p><strong>{business_data['business_name']}</strong></p>
                    <p>{business_data['address']}</p>
                    <p style="font-size: 13px; margin-top: 8px; color: #8b5a00;"><em>This is where you can scan the QR code. Enter your actual pickup address below.</em></p>
                </div>

                <form id="donation-form">
                    <div class="camera-container">
                        <label>📷 Food Photo <span class="required">*</span></label>
                        <div id="camera-preview">
                            <div>Click "Take Photo" to add photo</div>
                        </div>
                        <div class="camera-controls">
                            <button type="button" class="btn btn-primary" onclick="startCamera()">📷 Take Photo</button>
                            <button type="button" class="btn btn-secondary" onclick="clearPhoto()" style="display: none;" id="clear-btn">🗑️ Clear</button>
                        </div>
                        <input type="file" id="file-input" accept="image/*" onchange="handleFileSelect(event)">
                    </div>

                    <div class="form-group">
                        <label for="food-name">Food Name <span class="required">*</span></label>
                        <input type="text" id="food-name" name="food_name" placeholder="e.g., Pizza, Sandwiches, Salad" required>
                    </div>

                    <div class="form-group">
                        <label for="pickup-date">Pickup Date <span class="required">*</span></label>
                        <input type="date" id="pickup-date" name="pickup_date" required>
                    </div>

                    <div class="form-group">
                        <label for="pickup-time">Pickup Time <span class="required">*</span></label>
                        <input type="time" id="pickup-time" name="pickup_time" required>
                    </div>

                    <div class="form-group">
                        <label for="pickup-address">Pickup Address <span class="required">*</span></label>
                        <input type="text" id="pickup-address" name="pickup_address" placeholder="Enter your complete address where volunteers can pick up the food" required>
                        <small style="color: #666; font-size: 13px; margin-top: 5px; display: block;">Include street address, city, state, and ZIP code</small>
                    </div>

                    <div class="form-group">
                        <label for="food-notes">Additional Notes (Optional)</label>
                        <textarea id="food-notes" name="food_notes" placeholder="Any special notes, ingredients, or instructions..."></textarea>
                    </div>

                    <button type="submit" class="btn btn-success" id="submit-btn">
                        Submit Donation
                    </button>
                </form>

                <div id="loading" class="loading">
                    <div class="spinner"></div>
                    <p>Submitting your donation...</p>
                </div>
            </div>
        </div>

        <script>
            let currentStream = null;
            let capturedPhoto = null;
            const businessData = {{
                business_id: '{business_data['business_id']}',
                email: '{business_data['email']}',
                name: '{business_data['business_name']}',
                lat: {business_data['lat']},
                lng: {business_data['lng']},
                address: '{business_data['address']}'
            }};

            // Initialize form
            document.addEventListener('DOMContentLoaded', function() {{
                // Set date range: today to one week from today (disable previous dates)
                const today = new Date();
                const todayStr = today.toISOString().split('T')[0];
                
                const oneWeekLater = new Date(today);
                oneWeekLater.setDate(oneWeekLater.getDate() + 7);
                
                const dateInput = document.getElementById('pickup-date');
                dateInput.min = todayStr;  // Set minimum to today (prevents previous dates)
                dateInput.max = oneWeekLater.toISOString().split('T')[0];
                
                // Additional validation to prevent past dates
                dateInput.addEventListener('change', function() {{
                    const selectedDate = new Date(this.value);
                    const todayDate = new Date();
                    todayDate.setHours(0, 0, 0, 0);
                    selectedDate.setHours(0, 0, 0, 0);
                    
                    if (selectedDate < todayDate) {{
                        alert('Cannot select a date in the past. Please select today or a future date.');
                        this.value = todayStr;
                    }}
                }});
            }});

            function startCamera() {{
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
                    navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'environment' }} }})
                        .then(function(stream) {{
                            currentStream = stream;
                            const video = document.createElement('video');
                            video.srcObject = stream;
                            video.autoplay = true;
                            video.playsInline = true;
                            
                            const preview = document.getElementById('camera-preview');
                            preview.innerHTML = '';
                            preview.appendChild(video);
                            
                            const captureBtn = document.createElement('button');
                            captureBtn.className = 'btn btn-success';
                            captureBtn.textContent = '📸 Capture';
                            captureBtn.style.marginTop = '10px';
                            captureBtn.style.width = '100%';
                            captureBtn.onclick = function() {{ capturePhoto(video); }};
                            preview.appendChild(captureBtn);
                        }})
                        .catch(function(error) {{
                            console.error('Error accessing camera:', error);
                            showError('Unable to access camera. Please use gallery option.');
                        }});
                }} else {{
                    showError('Camera not supported. Please use the gallery option.');
                }}
            }}

            function capturePhoto(video) {{
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0);
                
                capturedPhoto = canvas.toDataURL('image/jpeg', 0.8);
                
                if (currentStream) {{
                    currentStream.getTracks().forEach(track => track.stop());
                    currentStream = null;
                }}
                
                const preview = document.getElementById('camera-preview');
                preview.innerHTML = '<img src="' + capturedPhoto + '" alt="Captured Photo">';
                document.getElementById('clear-btn').style.display = 'inline-block';
                
                showSuccess('Photo captured successfully!');
            }}

            function handleFileSelect(event) {{
                const file = event.target.files[0];
                if (file) {{
                    const reader = new FileReader();
                    reader.onload = function(e) {{
                        capturedPhoto = e.target.result;
                        const preview = document.getElementById('camera-preview');
                        preview.innerHTML = '<img src="' + capturedPhoto + '" alt="Selected Photo">';
                        document.getElementById('clear-btn').style.display = 'inline-block';
                        showSuccess('Photo selected successfully!');
                    }};
                    reader.readAsDataURL(file);
                }}
            }}

            function clearPhoto() {{
                capturedPhoto = null;
                document.getElementById('camera-preview').innerHTML = 
                    '<div>Click "Take Photo" to add photo</div>';
                document.getElementById('clear-btn').style.display = 'none';
                document.getElementById('file-input').value = '';
            }}

            function showError(message) {{
                const errorDiv = document.getElementById('error-message');
                errorDiv.textContent = message;
                errorDiv.classList.add('show');
                setTimeout(() => {{ errorDiv.classList.remove('show'); }}, 5000);
            }}

            function showSuccess(message) {{
                const successDiv = document.getElementById('success-message');
                successDiv.textContent = message;
                successDiv.classList.add('show');
                setTimeout(() => {{ successDiv.classList.remove('show'); }}, 3000);
            }}

            document.getElementById('donation-form').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                if (!capturedPhoto) {{
                    showError('Please take or select a photo of the food');
                    return;
                }}

                document.getElementById('loading').classList.add('show');
                document.getElementById('donation-form').style.display = 'none';
                document.getElementById('submit-btn').disabled = true;

                try {{
                    const formData = new FormData();
                    formData.append('food_name', document.getElementById('food-name').value);
                    formData.append('food_desc', document.getElementById('food-notes').value);
                    formData.append('pickup_date', document.getElementById('pickup-date').value);
                    formData.append('pickup_time', document.getElementById('pickup-time').value);
                    formData.append('pick_up_address', document.getElementById('pickup-address').value);
                    formData.append('pick_up_lat', businessData.lat);
                    formData.append('pick_up_lng', businessData.lng);
                    formData.append('business_id', businessData.business_id);
                    formData.append('business_email', businessData.email);
                    formData.append('photo', capturedPhoto);
                    formData.append('token', '{token}');

                    const response = await fetch('/qr_donate_food', {{
                        method: 'POST',
                        body: formData
                    }});

                    const result = await response.json();

                    if (result.error === false) {{
                        document.getElementById('loading').classList.remove('show');
                        document.getElementById('donation-form').style.display = 'none';
                        
                        const container = document.querySelector('.form-container');
                        container.innerHTML = `
                            <div style="text-align: center; padding: 40px 20px;">
                                <div style="font-size: 64px; margin-bottom: 20px;">🎉</div>
                                <h2 style="color: #28a745; margin-bottom: 15px;">Success!</h2>
                                <p style="color: #666; margin-bottom: 20px;">Your food donation has been posted successfully!</p>
                                <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                    <p style="color: #1976d2; margin-bottom: 10px;"><strong>What's Next?</strong></p>
                                    <p style="color: #424242; font-size: 14px;">Nearby recipients have been notified about your donation. They will contact you for pickup.</p>
                                </div>
                                <button onclick="location.reload()" class="btn btn-primary" style="width: 100%;">
                                    ➕ Donate More Food
                                </button>
                            </div>
                        `;
                    }} else {{
                        showError('Error: ' + result.message);
                        document.getElementById('loading').classList.remove('show');
                        document.getElementById('donation-form').style.display = 'block';
                        document.getElementById('submit-btn').disabled = false;
                    }}
                }} catch (error) {{
                    console.error('Error:', error);
                    showError('Network error. Please check your connection and try again.');
                    document.getElementById('loading').classList.remove('show');
                    document.getElementById('donation-form').style.display = 'block';
                    document.getElementById('submit-btn').disabled = false;
                }}
            }});
        </script>
    </body>
    </html>
            """