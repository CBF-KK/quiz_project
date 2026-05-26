from django.shortcuts import render
from .models import Question
import random


def home(request):

    score = None
    submitted = False

    # 第一次進入頁面
    if request.method == 'GET':

        # 取得所有題目
        all_questions = list(Question.objects.all())

        # 隨機排序
        random.shuffle(all_questions)

        # 抽10題
        questions = all_questions[:10]

        # 儲存題目順序
        request.session['question_ids'] = [q.id for q in questions]

    # 按提交後
    else:

        submitted = True
        score = 0

        # 取得原本題目順序
        question_ids = request.session.get('question_ids', [])

        # 依照原順序抓題目
        questions = []

        for qid in question_ids:
            questions.append(Question.objects.get(id=qid))

        # 計分
        for q in questions:

            user_answer = request.POST.get(str(q.id))

            if user_answer == q.answer:
                score += 100 / len(questions)

        score = round(score)

    return render(request, 'home.html', {
        'questions': questions,
        'score': score,
        'submitted': submitted
    })