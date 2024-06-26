from django.shortcuts import render, redirect
from .models import *
from django.contrib import messages
from .forms import *
import csv
from django.http import HttpResponse, JsonResponse
from django.views.generic.base import View
from csv import DictReader
from io import TextIOWrapper
from datetime import date, timedelta

# CRUD
# Import/Export csv files

def index(request):
    startdate = date.today()
    enddate = startdate + timedelta(days=7)
    todos = Todos.objects.filter(due_date__range=[startdate, enddate])
    return render(request, 'core/index.html', {'todos': todos})

def dashboard(request):
    return render(request, 'core/dashboard.html')

def record(request):
    if request.user.is_authenticated:
        records = Record.objects.all()
        context = {
            'records': records,
        }
        return render(request, 'core/record.html', context)
    else:
        messages.success(request, 'You must be logged in to see this')
        return redirect('index')

def client(request, pk):
    if request.user.is_authenticated:
        client_record = Record.objects.get(id=pk)
        todos = Todos.objects.filter(user_id=pk)
        todo_form = AddTodoForm(request.POST or None)
        interactions = Interaction.objects.filter(client_id=pk)
        interaction_form = AddInteractions(request.POST or None)
        transactions = Transaction.objects.filter(client_id=pk)
        transaction_form = AddTransaction(request.POST or None)
        if request.method == "POST":
            if 'todo' in request.POST:
                if todo_form.is_valid():
                    todo_form.instance.user_id = client_record.id
                    todo_form.save()
                    return redirect('index')
            elif 'interaction' in request.POST:
                if interaction_form.is_valid():
                    interaction_form.instance.client_id = client_record.id
                    interaction_form.save()
                    return redirect('record')
            elif 'transaction' in request.POST:
                if transaction_form.is_valid():
                    transaction_form.instance.client_id = client_record.id
                    transaction_form.instance.service = request.POST.get('service')
                    transaction_form.instance.amount = request.POST.get('amount')
                    transaction_form.save()
                #     new_item = "Newly Added Item"
                #     return JsonResponse({"newItem": new_item})
                # else:
                #     return JsonResponse({"error": "Invalid request method."}, status=400)
        return render(request, 'core/client.html', {
            'client_record': client_record, 
            'todos': todos, 
            'todo_form': todo_form,
            'interactions': interactions,
            'interaction_form': interaction_form,
            'transactions': transactions,
            'transaction_form': transaction_form,
            })
    else:
        messages.success(request, "You must be logged in to view this")
        return redirect('index')
    
def delete_client(request, pk):
    if request.user.is_authenticated:
        delete_record = Record.objects.get(id=pk)
        delete_record.delete()
        messages.success(request, 'Record has been deleted')
        return redirect('index')
    else:
        messages.success(request, 'You must be logged in to perform this action')

def add_client(request):
    form = AddRecordForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, 'Record added')
                return redirect('index')
            else:
                messages.success(request, 'There was an error filling the form, please try again')
                return redirect('record')
        else:
            return render(request, 'core/add.html', {'form': form})
    else:
        messages.success(request, 'You need to be logged in to add a record')
        return redirect('index')
    
def update_client(request, pk):
    if request.user.is_authenticated:
        current_record = Record.objects.get(id=pk)
        form = AddRecordForm(request.POST or None, instance=current_record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Record has been updated')
            return redirect('index')
        return render(request, 'core/update.html', {
            'form': form,
            'current_record': current_record,
            })
    else:
        messages.success(request, 'You must be logged in to update')
        return redirect('index')
    
def csv_record(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=records.csv'
    writer = csv.writer(response)
    records = Record.objects.all()
    writer.writerow(['Date Created', 'First Name', 'Last Name', 'Address', 'Email', 'Phone', 'Todo'])
    for record in records:
        writer.writerow([record.created_at.strftime("%d-%b-%Y"), record.full_name, record.biz_name, record.address, record.email, record.phone, record.todos])
    return response

def upload_csv_record(request):
    if request.user.is_authenticated:
        if request.method == "POST" and "records_file" in request.FILES:
            record_file = request.FILES["records_file"]
            rows = TextIOWrapper(record_file, encoding="utf-8", newline="")
            for row in DictReader(rows):
                import_email = row['email']
                if not Record.objects.filter(email=import_email).exists():
                    form = AddRecordForm(row)
                    form.save()
            messages.success(request, 'File has been uploaded')
            return redirect('index')
        else:
            return render(request, 'core/upload.html', {'form': UploadForm()})
    else:
        messages.success(request, 'You must be logged in to upload files')
        return redirect('index')
    
def search(request):
    if request.method == "POST":
        searched = request.POST["searched"]
        records = Record.objects.filter(full_name__contains=searched)
        return render(request, 'core/search.html', {
            'searched': searched,
            'records': records,
        })
    return render(request, 'core/search.html', {})

def add_todo(request):
    form = AddTodoForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                form.instance.user_id = request.user.id
                form.save()
                messages.success(request, 'Task added')
                return redirect('index')
            else:
                messages.success(request, 'There was an error filling the form, please try again')
                return redirect('record')
        else:
            return render(request, 'core/add.html', {'form': form})
    else:
        messages.success(request, 'You need to be logged in to add a record')
        return redirect('index')

def interact(request, pk):
    client = Record.objects.filter(id=pk)
    return render(request, 'core/interact.html', {'client': client})
