@extends('layouts.app')

@section('title', 'All Cities - SchoolList')
@section('meta_description', 'Browse schools by city. Find CBSE, ICSE and State Board schools across India.')

@section('content')
<section class="bg-gray-100 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-900">All Cities</h1>
        <p class="text-gray-600 mt-2">Browse schools by city across India</p>
    </div>
</section>

<section class="py-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            @foreach($cities as $city)
                @php
                    $citySlug = is_object($city) ? $city->slug : $city['slug'];
                    $cityName = is_object($city) ? $city->name : $city['name'];
                    $schoolCount = is_object($city) ? $city->school_count : ($city['school_count'] ?? 0);
                @endphp
                <a href="{{ route('city.show', $citySlug) }}" 
                   class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition group">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 class="font-semibold text-gray-900 group-hover:text-blue-600">{{ $cityName }}</h3>
                            <p class="text-sm text-gray-500 mt-1">{{ number_format($schoolCount) }} schools</p>
                        </div>
                        <svg class="w-5 h-5 text-gray-400 group-hover:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                        </svg>
                    </div>
                </a>
            @endforeach
        </div>
    </div>
</section>
@endsection
