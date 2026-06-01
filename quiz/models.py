from django.conf import settings
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
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
    )

    difficulty = models.CharField(
        "難易度",
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default="medium",
    )

    def __str__(self):
        return self.question_text or f"題目 {self.id}"


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="使用者",
        related_name="quiz_attempts",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user_attempt_number = models.PositiveIntegerField("使用者測驗編號", default=1)
    question_count = models.PositiveIntegerField("測驗題數", default=0)
    score = models.PositiveIntegerField("分數", default=0)
    correct_count = models.PositiveIntegerField("答對題數", default=0)
    started_at = models.DateTimeField("開始時間")
    finished_at = models.DateTimeField("完成時間", null=True, blank=True)
    duration_seconds = models.PositiveIntegerField("作答秒數", default=0)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        if self.user:
            return f"{self.user.username} - 第 {self.user_attempt_number} 次測驗"
        return f"未登入使用者 - {self.score} 分"


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        verbose_name="測驗紀錄",
        related_name="answers",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        Question,
        verbose_name="題目",
        on_delete=models.CASCADE,
    )
    display_number = models.PositiveIntegerField("題號")
    option_order = models.CharField("選項原始順序", max_length=20)

    user_answer = models.CharField("使用者答案", max_length=1, blank=True)
    user_display_answer = models.CharField("畫面顯示答案", max_length=1, blank=True)
    user_answer_text = models.CharField("使用者答案內容", max_length=255, blank=True)

    correct_answer = models.CharField("正確答案", max_length=1)
    correct_display_answer = models.CharField("畫面顯示正確答案", max_length=1)
    correct_answer_text = models.CharField("正確答案內容", max_length=255, blank=True)

    is_correct = models.BooleanField("是否答對", default=False)

    class Meta:
        ordering = ["display_number"]

    def __str__(self):
        return f"第 {self.display_number} 題"

    def get_option_text(self, key):
        option_map = {
                "A": self.question.option_a_text,
                "B": self.question.option_b_text,
                "C": self.question.option_c_text,
                "D": self.question.option_d_text,
        }
        return option_map.get(key, "")

    def get_option_image(self, key):
        option_map = {
            "A": self.question.option_a_image,
            "B": self.question.option_b_image,
            "C": self.question.option_c_image,
            "D": self.question.option_d_image,
        }
        return option_map.get(key)

    def get_user_answer_text(self):
        if self.user_answer_text:
            return self.user_answer_text
        return self.get_option_text(self.user_answer)

    def get_correct_answer_text(self):
        if self.correct_answer_text:
            return self.correct_answer_text
        return self.get_option_text(self.correct_answer)

    def get_user_answer_image(self):
        return self.get_option_image(self.user_answer)

    def get_correct_answer_image(self):
        return self.get_option_image(self.correct_answer)