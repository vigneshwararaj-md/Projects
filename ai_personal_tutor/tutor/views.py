# tutor/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from .models import Document, Conversation
from .ai_engine import RAGTutor
import os

# ------------------------------------------------------------
# HELPER FUNCTION
# ------------------------------------------------------------

def get_rag_tutor_for_document(document):
    tutor = RAGTutor()
    print(f"Processing PDF: {document.title}")
    tutor.process_pdf(document.pdf_file.path)
    return tutor


# ------------------------------------------------------------
# VIEW 1: DASHBOARD
# ------------------------------------------------------------

def dashboard(request):
    """
    THE DASHBOARD PAGE
    
    URL: http://127.0.0.1:8000/
    
    What this view does:
    1. Shows all documents the user has uploaded
    2. Lets user upload new PDFs
    
    Flow:
    User visits homepage → Sees their documents → Can upload new ones
    """
    
    # 🔗 CONNECTION: Django → SQL
    # Get all documents from the database
    # This Python code generates: SELECT * FROM tutor_document
    documents = Document.objects.all()
    
    # Check if user submitted the upload form
    if request.method == 'POST':
        title = request.POST.get('title')
        pdf_file = request.FILES.get('pdf_file')
        
        # Validate: Make sure both fields are filled
        if title and pdf_file:
            # 🔗 CONNECTION: Python → SQL (INSERT)
            # This creates a new row in the database
            # Generates: INSERT INTO tutor_document (title, pdf_file) VALUES (...)
            document = Document.objects.create(
                title=title,
                pdf_file=pdf_file
            )
            
            # Show success message to user
            messages.success(
                request, 
                f'✅ "{title}" uploaded successfully! Ready to study.'
            )
            
            # Redirect to the chat page for this document
            return redirect('chat', document_id=document.id)
        
        else:
            # Show error if fields are empty
            messages.error(request, 'Please provide both a title and a PDF file.')
    
    # Render the HTML page with the documents
    return render(request, 'tutor/dashboard.html', {
        'documents': documents
    })


# ------------------------------------------------------------
# VIEW 2: CHAT / ASK QUESTIONS
# ------------------------------------------------------------

def chat_view(request, document_id):
    """
    THE CHAT PAGE
    
    URL: http://127.0.0.1:8000/chat/1/
    
    What this view does:
    1. Shows conversation history for a document
    2. Lets user ask questions
    3. Calls AI engine to get answers
    4. Saves Q&A to database
    
    This is where ALL THREE components connect:
    Django (web) + SQL (database) + AI (RAGTutor)
    """
    
    # 🔗 CONNECTION: Python → SQL (SELECT)
    # Get the document from database, or show 404 error if not found
    # Generates: SELECT * FROM tutor_document WHERE id = document_id
    document = get_object_or_404(Document, id=document_id)
    
    # 🔗 CONNECTION: Python → SQL (SELECT with ORDER BY)
    # Get all conversations for this document, newest first
    # Generates: SELECT * FROM tutor_conversation 
    #            WHERE document_id = document_id 
    #            ORDER BY created_at DESC
    conversations = Conversation.objects.filter(
        document=document
    ).order_by('-created_at')
    
    # Variables to hold current question/answer
    current_question = None
    current_answer = None
    
    # Check if user asked a question
    if request.method == 'POST':
        question = request.POST.get('question')
        
        if question:
            # 🔗 CONNECTION: Django → AI Engine
            # This is where the magic happens!
            # Get the AI tutor for this document
            rag_tutor = get_rag_tutor_for_document(document)
            
            # Ask the AI for an answer
            print(f"User asked: {question}")
            answer = rag_tutor.ask_question(question)
            print(f"AI answered: {answer[:100]}...")
            
            # 🔗 CONNECTION: Python → SQL (INSERT)
            # Save this Q&A to the database
            # Generates: INSERT INTO tutor_conversation 
            #            (document_id, question, answer) VALUES (...)
            Conversation.objects.create(
                document=document,
                question=question,
                answer=answer
            )
            
            # Store for displaying on the page
            current_question = question
            current_answer = answer
            
            # Refresh conversations to include the new one
            conversations = Conversation.objects.filter(
                document=document
            ).order_by('-created_at')
    
    # Render the chat page
    return render(request, 'tutor/chat.html', {
        'document': document,
        'conversations': conversations,
        'current_question': current_question,
        'current_answer': current_answer,
    })


# ------------------------------------------------------------
# VIEW 3: DELETE DOCUMENT
# ------------------------------------------------------------

def delete_document(request, document_id):
    """
    DELETE A DOCUMENT
    
    URL: http://127.0.0.1:8000/delete/1/
    
    What this view does:
    1. Finds the document
    2. Deletes the physical PDF file
    3. Deletes the database record
    4. Redirects to dashboard
    """
    
    # Get the document or show 404
    document = get_object_or_404(Document, id=document_id)
    
    # Delete the actual PDF file from the server
    if document.pdf_file:
        if os.path.isfile(document.pdf_file.path):
            os.remove(document.pdf_file.path)
            print(f"Deleted file: {document.pdf_file.path}")
    
    # 🔗 CONNECTION: Python → SQL (DELETE)
    # Delete from database - also deletes related conversations (CASCADE)
    # Generates: DELETE FROM tutor_document WHERE id = document_id
    document.delete()
    
    messages.success(request, f'"{document.title}" deleted successfully.')
    
    # Go back to dashboard
    return redirect('dashboard')