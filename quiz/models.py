from django.conf import settings
from django.db import models

# 題目資料表，儲存題目文字、圖片、四個選項、正確答案與難度
class Question(models.Model):

    # 題目難易度選項
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
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")], # 正確答案只能是 A、B、C 或 D
    )

    difficulty = models.CharField(
        "難易度",
        max_length=10,
        choices=DIFFICULTY_CHOICES,  # 難易度只能是 easy、medium 或 hard
        default="medium",            # 預設難易度為中等
    )
    
    # 在後台或查詢資料時，顯示題目文字；若沒有文字則顯示題目 id
    def __str__(self):
        return self.question_text or f"題目 {self.id}" 

# 測驗紀錄資料表，包含使用者、測驗編號、題數、分數、答對題數、開始時間、完成時間和作答秒數
class QuizAttempt(models.Model):

    # 一個使用者可以有多次測驗紀錄，每次測驗紀錄會有一個獨立的測驗編號，根據這個編號來區分同一使用者的不同測驗次數
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="使用者",
        related_name="quiz_attempts",
        on_delete=models.CASCADE,
    )
    user_attempt_number = models.PositiveIntegerField("使用者測驗編號", default=1) # 同一使用者的測驗紀錄會根據這個編號區分不同的測驗次數
    question_count = models.PositiveIntegerField("測驗題數", default=0) 
    score = models.PositiveIntegerField("分數", default=0) 
    correct_count = models.PositiveIntegerField("答對題數", default=0) # 根據答對題數計算
    started_at = models.DateTimeField("開始時間") 
    finished_at = models.DateTimeField("完成時間", null=True, blank=True)
    duration_seconds = models.PositiveIntegerField("作答秒數", default=0) 

    # 預設依開始時間由新到舊排序
    class Meta:
        ordering = ["-started_at"] 

    # 顯示這筆測驗紀錄的簡短名稱
    def __str__(self):
        return f"{self.user.username} - 第 {self.user_attempt_number} 次測驗"

# 作答明細資料表，包含測驗紀錄、題目、題號、選項原始順序、使用者答案、使用者畫面顯示答案、使用者答案內容、正確答案、正確畫面顯示答案、正確答案內容和是否答對
class QuizAnswer(models.Model):
    # 每個測驗紀錄會有多個測驗答案，每個測驗答案對應一個題目，根據測驗紀錄和題目來區分不同的測驗答案
    attempt = models.ForeignKey(
        QuizAttempt, 
        verbose_name="測驗紀錄", #
        related_name="answers",
        on_delete=models.CASCADE, #
    )
    # 每個測驗答案對應一個題目，根據題目來區分不同的測驗答案
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
    
    # 同一次測驗內，依題號排序作答紀錄
    class Meta:
        ordering = ["display_number"]

    # 顯示這筆作答明細的題號
    def __str__(self):
        return f"第 {self.display_number} 題"

    # 依照 A、B、C、D 取得對應選項文字
    def get_option_text(self, key):
        option_map = {
                "A": self.question.option_a_text,
                "B": self.question.option_b_text,
                "C": self.question.option_c_text,
                "D": self.question.option_d_text,
        }
        return option_map.get(key, "")

    # 依照 A、B、C、D 取得對應選項圖片
    def get_option_image(self, key):
        option_map = {
            "A": self.question.option_a_image,
            "B": self.question.option_b_image,
            "C": self.question.option_c_image,
            "D": self.question.option_d_image,
        }
        return option_map.get(key)

    # 取得使用者答案文字；若已儲存文字就直接使用，否則從題目選項取得
    def get_user_answer_text(self):
        if self.user_answer_text:
            return self.user_answer_text
        return self.get_option_text(self.user_answer)

    # 取得正確答案文字；若已儲存文字就直接使用，否則從題目選項取得
    def get_correct_answer_text(self):
        if self.correct_answer_text:
            return self.correct_answer_text
        return self.get_option_text(self.correct_answer)
    
    # 取得使用者答案圖片
    def get_user_answer_image(self):
        return self.get_option_image(self.user_answer)

    # 取得正確答案圖片
    def get_correct_answer_image(self):
        return self.get_option_image(self.correct_answer)