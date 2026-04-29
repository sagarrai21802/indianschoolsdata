@extends('layouts.app')

@section('title', 'SchoolList - Find Best Schools in India')
@section('meta_description', 'Find top CBSE, ICSE, and State Board schools in India. Search by city, locality, board type, fees and ratings.')

@section('content')
<!-- Hero Section -->
<section class="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 class="text-4xl md:text-5xl font-bold mb-6">
            Find the Best Schools in India
        </h1>
        <p class="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Comprehensive directory of CBSE, ICSE, and State Board schools. 
            Search by city, locality, fees, and ratings.
        </p>
        
        <!-- Search Box -->
        <div class="max-w-2xl mx-auto">
            <form action="{{ route('search') }}" method="GET" class="flex">
                <input type="text" name="q" placeholder="Search schools by name, city, or board..."
                    class="flex-1 px-6 py-4 rounded-l-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-400">
                <button type="submit" class="bg-orange-500 hover:bg-orange-600 px-8 py-4 rounded-r-lg font-semibold transition">
                    Search
                </button>
            </form>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 max-w-3xl mx-auto">
            <div class="bg-white/10 rounded-lg p-4">
                <div class="text-3xl font-bold">{{ number_format($totalSchools ?? 0) }}</div>
                <div class="text-blue-100">Schools Listed</div>
            </div>
            <div class="bg-white/10 rounded-lg p-4">
                <div class="text-3xl font-bold">{{ number_format($totalCities ?? 0) }}</div>
                <div class="text-blue-100">Cities Covered</div>
            </div>
            <div class="bg-white/10 rounded-lg p-4">
                <div class="text-3xl font-bold">50+</div>
                <div class="text-blue-100">Board Types</div>
            </div>
        </div>
    </div>
</section>

<!-- Featured Cities -->
<section class="py-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12">Popular Cities</h2>
        
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
            @foreach($featuredCities as $city)
                @php
                    $citySlug = is_object($city) ? $city->slug : $city['slug'];
                    $cityName = is_object($city) ? $city->name : $city['name'];
                    $schoolCount = is_object($city) ? $city->school_count : ($city['school_count'] ?? 0);
                @endphp
                <a href="{{ route('city.show', $citySlug) }}" 
                   class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition text-center group">
                    <div class="text-4xl mb-3">🏫</div>
                    <h3 class="font-semibold text-gray-900 group-hover:text-blue-600">{{ $cityName }}</h3>
                    <p class="text-sm text-gray-500 mt-1">{{ number_format($schoolCount) }} schools</p>
                </a>
            @endforeach
        </div>

        <div class="text-center mt-8">
            <a href="{{ route('schools.index') }}" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium">
                View All Cities
                <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
            </a>
        </div>
    </div>
</section>

<!-- Board Types -->
<section class="py-16 bg-gray-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12">Browse by Board</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <a href="{{ route('search', ['board' => 'CBSE']) }}" class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
                <h3 class="text-xl font-semibold mb-2">CBSE Schools</h3>
                <p class="text-gray-600">Central Board of Secondary Education - India's national curriculum board.</p>
            </a>
            
            <a href="{{ route('search', ['board' => 'ICSE']) }}" class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
                <h3 class="text-xl font-semibold mb-2">ICSE Schools</h3>
                <p class="text-gray-600">Indian Certificate of Secondary Education - comprehensive curriculum.</p>
            </a>
            
            <a href="{{ route('search', ['board' => 'State Board']) }}" class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
                <h3 class="text-xl font-semibold mb-2">State Board Schools</h3>
                <p class="text-gray-600">Regional state education boards with local curriculum.</p>
            </a>
        </div>
    </div>
</section>

<!-- Featured Schools -->
@if(isset($featuredSchools) && $featuredSchools->count() > 0)
<section class="py-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12">Featured Schools</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            @foreach($featuredSchools as $school)
                @include('components.school-card', ['school' => $school])
            @endforeach
        </div>
    </div>
</section>
@endif
@endsection
