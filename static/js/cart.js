// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    const applyButton = document.getElementById('apply-coupon');
    if (applyButton) {
        applyButton.addEventListener('click', applyCoupon);
    }
});

function applyCoupon() {
    const couponCode = document.getElementById('coupon_code').value.trim();
    const messageDiv = document.getElementById('coupon-message');
    const discountRow = document.getElementById('discount-row');
    const discountAmount = document.getElementById('discount-amount');
    const finalTotal = document.getElementById('final-total');
    const appliedCouponInput = document.getElementById('applied_coupon');
    const currency = document.querySelector('[data-total]').textContent.split(' ').pop();

    // Validate coupon code
    if (!couponCode) {
        messageDiv.innerHTML = '<div class="alert alert-danger mt-2">الرجاء إدخال كود الخصم</div>';
        return;
    }

    // Clear previous messages
    messageDiv.innerHTML = '';
    messageDiv.className = '';

    // Show loading message
    messageDiv.innerHTML = '<div class="alert alert-info mt-2">جاري التحقق من الكود...</div>';

    // Make API call to validate and apply coupon
    fetch('/cart/apply-coupon', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ coupon_code: couponCode })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Show success message
            messageDiv.innerHTML = `<div class="alert alert-success mt-2">تم تطبيق الخصم بنجاح!</div>`;
            
            // Update discount display
            discountRow.style.display = 'flex';
            discountAmount.textContent = `${data.discount_amount} ${currency}`;
            finalTotal.textContent = `${data.final_total} ${currency}`;
            
            // Store applied coupon
            appliedCouponInput.value = couponCode;
        } else {
            // Show error message
            messageDiv.innerHTML = `<div class="alert alert-danger mt-2">${data.message}</div>`;
            
            // Reset discount display
            discountRow.style.display = 'none';
            discountAmount.textContent = `0 ${currency}`;
            finalTotal.textContent = `${document.querySelector('[data-total]').dataset.total} ${currency}`;
            
            // Clear applied coupon
            appliedCouponInput.value = '';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        messageDiv.innerHTML = '<div class="alert alert-danger mt-2">حدث خطأ أثناء تطبيق الكوبون</div>';
        
        // Reset on error
        discountRow.style.display = 'none';
        discountAmount.textContent = `0 ${currency}`;
        finalTotal.textContent = `${document.querySelector('[data-total]').dataset.total} ${currency}`;
        appliedCouponInput.value = '';
    });
}
