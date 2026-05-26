from django.db import models

class Question(models.Model):

    # 題目
    question_text = models.CharField(max_length=255, blank=True)
    question_image = models.ImageField(upload_to='questions/', blank=True, null=True)

    # A
    option_a_text = models.CharField(max_length=100, blank=True)
    option_a_image = models.ImageField(upload_to='options/', blank=True, null=True)

    # B
    option_b_text = models.CharField(max_length=100, blank=True)
    option_b_image = models.ImageField(upload_to='options/', blank=True, null=True)

    # C
    option_c_text = models.CharField(max_length=100, blank=True)
    option_c_image = models.ImageField(upload_to='options/', blank=True, null=True)

    # D
    option_d_text = models.CharField(max_length=100, blank=True)
    option_d_image = models.ImageField(upload_to='options/', blank=True, null=True)

    # 正確答案
    answer = models.CharField(max_length=1)

    def __str__(self):
        return self.question_text or "圖片題目"