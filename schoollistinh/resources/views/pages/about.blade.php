@extends('layouts.app')

@section('title', 'About Us - SchoolList')
@section('meta_description', 'SchoolList is India\'s comprehensive school directory. Find CBSE, ICSE and State Board schools with fees, reviews and admission details.')

@section('content')
<section class="bg-blue-600 text-white py-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 class="text-4xl font-bold mb-4">About SchoolList</h1>
        <p class="text-xl text-blue-100">India's most comprehensive school directory</p>
    </div>
</section>

<section class="py-16">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="prose prose-lg mx-auto">
            <h2 class="text-2xl font-bold mb-4">Our Mission</h2>
            <p class="text-gray-600 mb-6">
                SchoolList aims to be the most comprehensive and trusted school directory in India. 
                We help parents find the best educational institutions for their children by providing 
                detailed information about schools across the country.
            </p>

            <h2 class="text-2xl font-bold mb-4">What We Offer</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div class="bg-gray-50 p-6 rounded-lg">
                    <h3 class="font-semibold mb-2">Comprehensive Listings</h3>
                    <p class="text-gray-600 text-sm">
                        Detailed information about CBSE, ICSE, State Board and international schools 
                        including fees, facilities, and admission details.
                    </p>
                </div>
                <div class="bg-gray-50 p-6 rounded-lg">
                    <h3 class="font-semibold mb-2">Easy Search</h3>
                    <p class="text-gray-600 text-sm">
                        Search schools by city, locality, board type, fees range, and ratings 
                        to find the perfect match for your child.
                    </p>
                </div>
                <div class="bg-gray-50 p-6 rounded-lg">
                    <h3 class="font-semibold mb-2">Verified Information</h3>
                    <p class="text-gray-600 text-sm">
                        We regularly update school information to ensure accuracy and reliability 
                        of the data provided to parents.
                    </p>
                </div>
                <div class="bg-gray-50 p-6 rounded-lg">
                    <h3 class="font-semibold mb-2">Direct Connect</h3>
                    <p class="text-gray-600 text-sm">
                        Connect directly with schools through our inquiry system to get admission 
                        information and schedule visits.
                    </p>
                </div>
            </div>

            <h2 class="text-2xl font-bold mb-4">Coverage</h2>
            <p class="text-gray-600 mb-6">
                We currently list schools across 70+ cities in India, including major metros like 
                Delhi, Mumbai, Bangalore, Hyderabad, Chennai, Pune, Kolkata and many more. 
                Our database includes thousands of schools from all major education boards.
            </p>
        </div>
    </div>
</section>
@endsection
