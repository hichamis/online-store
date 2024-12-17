document.addEventListener('DOMContentLoaded', function() {
    // تحسين تفاعل النجوم في نموذج التقييم
    const ratingInputs = document.querySelectorAll('.rating-input input');
    const ratingLabels = document.querySelectorAll('.rating-input label img');
    const str1Path = ratingLabels[0].src.replace('str2.png', 'str1.png');
    const str2Path = ratingLabels[0].src;

    // تحديث النجوم عند تحريك الماوس
    ratingLabels.forEach((label, index) => {
        label.parentElement.addEventListener('mouseover', () => {
            for (let i = ratingLabels.length - 1; i >= index; i--) {
                ratingLabels[i].src = str1Path;
            }
            for (let i = index - 1; i >= 0; i--) {
                ratingLabels[i].src = str2Path;
            }
        });

        label.parentElement.addEventListener('mouseout', () => {
            ratingLabels.forEach((star, i) => {
                if (!ratingInputs[i].checked) {
                    star.src = str2Path;
                }
            });
            updateStarsFromInput();
        });
    });

    // تحديث النجوم عند اختيار تقييم
    ratingInputs.forEach(input => {
        input.addEventListener('change', updateStarsFromInput);
    });

    function updateStarsFromInput() {
        const checkedInput = document.querySelector('.rating-input input:checked');
        if (checkedInput) {
            const rating = parseInt(checkedInput.value);
            ratingLabels.forEach((star, index) => {
                if (index >= ratingLabels.length - rating) {
                    star.src = str1Path;
                } else {
                    star.src = str2Path;
                }
            });
        }
    }

    // تحديث النجوم عند تحميل الصفحة
    updateStarsFromInput();
});
