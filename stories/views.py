from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Startup, Story, Category

@login_required
def story_wizard_view(request):
    if request.method == 'POST':
        # Simple extraction for Phase 1 demo
        startup = Startup.objects.create(
            founder=request.user,
            startup_name=request.POST.get('startup_name'),
            industry=request.POST.get('industry'),
            founded_year=request.POST.get('founded_year') or None,
            team_size=request.POST.get('team_size') or None,
            website=request.POST.get('website'),
        )
        
        Story.objects.create(
            author=request.user,
            startup=startup,
            title=request.POST.get('title'),
            summary=request.POST.get('summary'),
            problem_solved=request.POST.get('problem_solved'),
            timeline_content=request.POST.get('timeline_content'),
            challenges=request.POST.get('challenges'),
            failure_reason=request.POST.get('failure_reason'),
            lessons=request.POST.get('lessons'),
            future_plans=request.POST.get('future_plans'),
        )
        return redirect('home') # Redirect to home or dashboard after submit
        
    return render(request, 'stories/wizard.html')
