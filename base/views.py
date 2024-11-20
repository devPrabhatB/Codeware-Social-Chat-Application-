from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm 
from collections import defaultdict

# Create your views here.




def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, "User doesnot exist.")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Username or Password does not exists!")

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    # page = 'register'
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error ocurred during registration!!')

    return render(request, 'base/login_register.html', {'form': form})



# def home(request):
#     q = request.GET.get('q') if request.GET.get('q') != None else ''

#     rooms = Room.objects.filter(
#         Q(topic__name__icontains=q) |
#         Q(name__icontains=q) |
#         Q(description__icontains=q)
#         )

#     topics = Topic.objects.all() [0:5]
#     room_count = rooms.count()
#     room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

#     context = {'rooms': rooms, 'topics': topics, 'room_count': room_count,
#                'room_messages': room_messages}
#     return render(request, 'base/home.html', context)





# Define Jaccard Similarity function
def jaccard_similarity(query_set, target_set):
    intersection = len(query_set.intersection(target_set))
    union = len(query_set.union(target_set))
    return intersection / union if union != 0 else 0

def home(request):
    # Retrieve search query
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    
    # Split the query into words for Jaccard similarity calculation
    query_words = set(q.lower().split())

    # Retrieve all rooms initially
    rooms = Room.objects.all()

    # Dictionary to hold rooms with their similarity scores
    room_similarity_scores = defaultdict(float)

    # Calculate Jaccard similarity for each room based on topic, name, and description
    for room in rooms:
        # Combine all relevant fields into a single set of keywords
        room_keywords = set()
        room_keywords.update(room.topic.name.lower().split())  # Add topic keywords
        room_keywords.update(room.name.lower().split())        # Add name keywords
        room_keywords.update(room.description.lower().split()) # Add description keywords

        # Calculate similarity with the query
        similarity = jaccard_similarity(query_words, room_keywords)
        room_similarity_scores[room] = similarity

    # Filter rooms with similarity above a certain threshold (e.g., 0.1) and order them by similarity
    filtered_rooms = sorted(
        [room for room, score in room_similarity_scores.items() if score > 0.1],
        key=lambda x: room_similarity_scores[x],
        reverse=True
    )

    # Fallback to all rooms if no relevant rooms are found
    if not filtered_rooms:
        filtered_rooms = rooms

    # Topics and count
    topics = Topic.objects.all() [0:5]
    room_count = len(filtered_rooms)

    # Room messages filtered by the search query
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {
        'rooms': filtered_rooms,
        'topics': topics,
        'room_count': room_count,
        'room_messages': room_messages,
    }
    return render(request, 'base/home.html', context)



def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user= request.user,
            room= room,
            body= request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 
               'participants': participants} 
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages,
               'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')

def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        room_name = request.POST.get('name')

        # Check if topic or room name is empty
        if not topic_name or not room_name:
            messages.error(request, 'Cannot create a room!!')

        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=room_name,
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not allowed to make updates here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed to make changes here!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed to make changes here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    context = {'form': form}
    return render(request, 'base/update-user.html', context)

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html',{'topics': topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})
