from django.db import models


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "易"),
        ("medium", "中"),
        ("hard", "難"),
    ]

    question_text = models.CharField("題目文字", max_length=255, blank=True)
    question_image = models.ImageField("題目圖片", upload_to="questions/", blank=True, null=True)

    option_a_text = models.CharField("A 選項文字", max_length=100, blank=True)
    option_a_image = models.ImageField("A 選項圖片", upload_to="options/", blank=True, null=True)

    option_b_text = models.CharField("B 選項文字", max_length=100, blank=True)
    option_b_image = models.ImageField("B 選項圖片", upload_to="options/", blank=True, null=True)

    option_c_text = models.CharField("C 選項文字", max_length=100, blank=True)
    option_c_image = models.ImageField("C 選項圖片", upload_to="options/", blank=True, null=True)

    option_d_text = models.CharField("D 選項文字", max_length=100, blank=True)
    option_d_image = models.ImageField("D 選項圖片", upload_to="options/", blank=True, null=True)

    answer = models.CharField(
        "正確答案",
        max_length=1,
        choices=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
        ],
    )

    difficulty = models.CharField(
        "難易度",
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default="medium",
    )

    def __str__(self):
        return self.question_text or f"題目 {self.id}"