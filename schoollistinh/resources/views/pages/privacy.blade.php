@extends('layouts.app')

@section('title', 'Privacy Policy - SchoolList')
@section('meta_description', 'Privacy Policy for SchoolList. Learn how we collect, use and protect your personal information.')

@section('content')
<section class="bg-gray-100 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold">Privacy Policy</h1>
    </div>
</section>

<section class="py-12">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="prose prose-lg mx-auto">
            <p class="text-gray-600 mb-6">
                This Privacy Policy describes how SchoolList collects, uses, and protects your personal information.
            </p>

            <h2 class="text-xl font-bold mb-4">Information We Collect</h2>
            <p class="text-gray-600 mb-4">
                We collect information that you provide directly to us, including:
            </p>
            <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
                <li>Name and contact information when you submit inquiries</li>
                <li>Search queries and browsing behavior on our platform</li>
                <li>Device and browser information</li>
            </ul>

            <h2 class="text-xl font-bold mb-4">How We Use Your Information</h2>
            <p class="text-gray-600 mb-4">
                We use the collected information to:
            </p>
            <ul class="list-disc list-inside text-gray-600 mb-6 space-y-2">
                <li>Connect you with schools you inquire about</li>
                <li>Improve our services and user experience</li>
                <li>Send relevant updates and communications</li>
            </ul>

            <h2 class="text-xl font-bold mb-4">Data Security</h2>
            <p class="text-gray-600 mb-6">
                We implement appropriate security measures to protect your personal information 
                from unauthorized access, alteration, or disclosure.
            </p>

            <h2 class="text-xl font-bold mb-4">Contact Us</h2>
            <p class="text-gray-600">
                If you have any questions about this Privacy Policy, please contact us at 
                <a href="mailto:support@schoollist.in" class="text-blue-600 hover:underline">support@schoollist.in</a>.
            </p>
        </div>
    </div>
</section>
@endsection
