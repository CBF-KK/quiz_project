from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Question, QuizAttempt, QuizAnswer
import random

# 取得指定選項(A~D)的文字與圖片資料
def get_option(q, key):
    option_map = {
        "A": {"key": "A", "text": q.option_a_text, "image": q.option_a_image},
        "B": {"key": "B", "text": q.option_b_text, "image": q.option_b_image},
        "C": {"key": "C", "text": q.option_c_text, "image": q.option_c_image},
        "D": {"key": "D", "text": q.option_d_text, "image": q.option_d_image},
    }
    return option_map[key].copy()

# 建立前端顯示所需的題目資料結構
# 包含題目內容、隨機選項、使用者答案、正確答案與答題結果
def build_question_data(questions, option_orders, request=None, submitted=False):
    question_data = []
    display_keys = ["A", "B", "C", "D"]

    # 逐題整理選項顯示順序、使用者答案與正確答案
    for q in questions:

        # 依照 session 中儲存的順序顯示選項；若找不到資料，就使用預設 A~D
        order = option_orders.get(str(q.id), ["A", "B", "C", "D"])
        options = [get_option(q, key) for key in order]

        # display_key 是畫面上看到的 A~D；value 則保留原始答案代號
        for index, option in enumerate(options):
            option["display_key"] = display_keys[index]
            option["value"] = option["key"]

        user_answer = None               # 使用者的答案選項，用來判斷是否答對
        user_display_answer = None       # 使用者答案的畫面顯示選項鍵，用來在結果頁顯示使用者選的選項（A、B、C、D）
        user_option = None               # 使用者選擇的選項資料，用來在結果頁顯示使用者選的選項內容與圖片
        is_correct = None                # 是否答對，用來在結果頁顯示答題結果（答對或答錯）

        # 測驗送出後，從 POST 取得使用者答案並判斷是否答對
        if submitted and request is not None:
            user_answer = request.POST.get(str(q.id), "")
            is_correct = user_answer == q.answer

            # 找出使用者選到的選項，方便結果頁顯示選項文字與畫面上的代號
            for option in options:
                if option["value"] == user_answer:
                    user_display_answer = option["display_key"]
                    user_option = option

        # 找出正確答案在目前亂序後對應的顯示選項
        correct_option = None
        for option in options:
            if option["key"] == q.answer:
                correct_option = option
        
        question_data.append({
            "question": q,
            "options": options,
            "option_order": order,
            "user_answer": user_answer,
            "user_display_answer": user_display_answer, 
            "user_option": user_option,
            "correct_answer": q.answer,
            "correct_option": correct_option,
            "is_correct": is_correct,
        })

    return question_data # 傳回題目資料列表，供前端顯示使用

# 首頁與測驗主流程
# GET：顯示開始畫面或產生新測驗題目
# POST：接收作答結果、計分、儲存作答紀錄
@login_required
def home(request):
    score = None                    # 首頁初始分數為 None，只有在提交測驗後才會計算分數並顯示
    submitted = False               # 是否提交測驗，首頁初始為 False，只有在提交測驗後才會變為 True
    question_data = []              # 首頁初始不顯示題目，只有在點擊開始測驗後才會顯示題目
    duration_seconds = None         # 作答秒數，首頁初始為 None，只有在提交測驗後才會計算作答秒數並顯示
    attempt = None                  # 測驗紀錄，首頁初始為 None，只有在提交測驗後才會建立測驗紀錄並顯示
    time_limit_seconds = 600        # 時間限制秒數，首頁初始為 600 秒
    selected_count = 10             # 選擇的題目數量，首頁初始為 10 題


    # 使用 GET 開始一份新測驗
    if request.method == "GET":

        # 沒有 start=1 時，只顯示等待開始的畫面
        if request.GET.get("start") != "1":
            return render(request, "home.html", {
                "question_data": [],
                "score": score,
                "submitted": submitted,
                "duration_seconds": duration_seconds,
                "attempt": attempt,
                "time_limit_seconds": time_limit_seconds,
                "waiting_to_start": True,                           # 是否等待開始測驗，首頁初始為 True，只有在點擊開始測驗後才會變為 False
                "selected_count": selected_count,
            })
        
        # 讀取使用者選擇的題數，預設為 10 題
        try:
            count = int(request.GET.get("count", 10))
        except ValueError:
            count = 10
        if count not in [5, 10]:
            count = 10

        # 根據 count 參數來記錄選擇的題目數量，這樣在前端就可以顯示使用者選擇的題目數量
        selected_count = count

        # 題數不同，測驗時間也不同
        if count == 5:
            time_limit_seconds = 300
        else:
            time_limit_seconds = 600

        all_questions = list(Question.objects.all()) # 從資料庫中取得所有題目，這樣才能根據使用者的錯題紀錄來選擇題目

        # 錯題優先機制
        # 優先安排使用者曾經答錯的題目，再補足其他隨機題目
        wrong_question_ids = request.session.get("wrong_question_ids", [])
        wrong_questions = list(Question.objects.filter(id__in=wrong_question_ids)) 

        wrong_question_map = {q.id: q for q in wrong_questions} 
        ordered_wrong_questions = [
            wrong_question_map[qid]
            for qid in wrong_question_ids
            if qid in wrong_question_map
        ]

        other_questions = [q for q in all_questions if q.id not in wrong_question_ids]

        random.shuffle(ordered_wrong_questions)
        random.shuffle(other_questions)

        questions = (ordered_wrong_questions + other_questions)[:count]

        # 建立選項原始順序的字典，根據題目 ID 來記錄選項的原始順序
        option_orders = {}
        for q in questions:
            option_keys = ["A", "B", "C", "D"]
            random.shuffle(option_keys)
            option_orders[str(q.id)] = option_keys

        # 將本次測驗需要用到的狀態存到 session
        # 題目順序、選項順序、開始時間與時間限制
        request.session["question_ids"] = [q.id for q in questions]
        request.session["option_orders"] = option_orders
        request.session["quiz_started_at"] = timezone.now().isoformat()
        request.session["time_limit_seconds"] = time_limit_seconds

        question_data = build_question_data(questions, option_orders)

    # 使用 POST 處理測驗送出
    else:
        submitted = True

        question_ids = request.session.get("question_ids", [])
        option_orders = request.session.get("option_orders", {})
        started_at_text = request.session.get("quiz_started_at")
        time_limit_seconds = request.session.get("time_limit_seconds", 300)

        if started_at_text:
            started_at = timezone.datetime.fromisoformat(started_at_text)
        else:
            started_at = timezone.now() #

        # 計算本次測驗花費時間
        finished_at = timezone.now() 
        duration_seconds = max(0, int((finished_at - started_at).total_seconds()))

        questions_map = {
            q.id: q
            for q in Question.objects.filter(id__in=question_ids)
        }

        questions = [
            questions_map[qid]
            for qid in question_ids
            if qid in questions_map
        ]

        question_data = build_question_data(
            questions,
            option_orders,
            request=request,
            submitted=True,
        )

        wrong_question_ids = request.session.get("wrong_question_ids", [])
        correct_count = 0

        # 統計答對題數，並更新錯題清單
        for item in question_data:
            q = item["question"]

            if item["is_correct"]:
                correct_count += 1

                if q.id in wrong_question_ids:
                    wrong_question_ids.remove(q.id)
            else:
                if q.id not in wrong_question_ids:
                    wrong_question_ids.append(q.id)

        request.session["wrong_question_ids"] = wrong_question_ids

        # 根據答對題數和題目總數來計算分數
        if questions:
            score = round(correct_count / len(questions) * 100) 
        else:
            score = 0

        next_attempt_number = (
            QuizAttempt.objects.filter(user=request.user).count() + 1
        )

        # 建立本次測驗紀錄
        attempt = QuizAttempt.objects.create(
            user=request.user,
            user_attempt_number=next_attempt_number,
            question_count=len(questions),
            score=score,
            correct_count=correct_count,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
        )

        # 逐題儲存作答明細
        for index, item in enumerate(question_data, start=1):
            QuizAnswer.objects.create(
                attempt=attempt,
                question=item["question"],
                display_number=index,
                option_order=",".join(item["option_order"]),
                user_answer=item["user_answer"] or "",
                user_display_answer=item["user_display_answer"] or "",
                user_answer_text=item["user_option"]["text"] if item["user_option"] else "",
                correct_answer=item["correct_answer"],
                correct_display_answer=item["correct_option"]["display_key"],
                correct_answer_text=item["correct_option"]["text"] if item["correct_option"] else "",
                is_correct=item["is_correct"],
            )

    return render(request, "home.html", {
        "question_data": question_data,
        "score": score,
        "submitted": submitted,
        "duration_seconds": duration_seconds,
        "attempt": attempt,
        "time_limit_seconds": time_limit_seconds,
        "waiting_to_start": False,
        "selected_count": selected_count,
    })

# 顯示目前登入使用者的歷史測驗紀錄
@login_required
def history(request):
    attempts = (
        QuizAttempt.objects
        .filter(user=request.user)
        .prefetch_related("answers", "answers__question")
        .order_by("-started_at")
    )

    return render(request, "history.html", {
        "attempts": attempts,
    })

# 註冊新使用者；註冊成功後自動登入並導回首頁
def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {
        "form": form,
    })

# 使用 Django 內建登入表單驗證帳號密碼，成功後導回首頁
def login_user(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )

            if user is not None:
                login(request, user)
                return redirect("home")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {
        "form": form,
    })

# 登出目前使用者，並導回登入頁面
def logout_user(request):
    logout(request)
    return redirect("login")