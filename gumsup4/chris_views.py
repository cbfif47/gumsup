from django.views.generic import ListView
from django.core.cache import cache
from gumsup4.base.models import CreativeWork, VisitorCounter
from django.db.models import F

class ChrisHomeView(ListView):
    model = CreativeWork
    template_name = "chris/home.html"
    context_object_name = "works"

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by work type
        work_type = self.request.GET.get("type")
        if work_type in ['music', 'painting', 'coding', 'other']:
            queryset = queryset.filter(work_type=work_type)
            
        # Filter by status
        status = self.request.GET.get("status")
        if status in ['in_progress', 'completed']:
            queryset = queryset.filter(status=status)
            
        # Randomize order (already default ordering='?', but we can make it explicit)
        queryset = queryset.order_by('?')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Visitor counter
        try:
            counter, created = VisitorCounter.objects.get_or_create(name='chris_home', defaults={'count': 1})
            
            # Only increment if the user has not visited during this session
            if not self.request.session.get('has_visited_chris', False):
                self.request.session['has_visited_chris'] = True
                VisitorCounter.objects.filter(name='chris_home').update(count=F('count') + 1)
                counter.refresh_from_db()
                
            visitor_count = counter.count
        except Exception:
            visitor_count = 47
            
        # Format visitor count as a 6-digit padded string
        padded_counter = str(visitor_count).zfill(6)
        context["visitor_digits"] = list(padded_counter)
        
        context["selected_type"] = self.request.GET.get("type", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["work_types"] = CreativeWork.WORK_TYPES
        context["status_choices"] = CreativeWork.STATUS_CHOICES
        
        return context
