@extends('layouts.app')

@php
$schoolName = is_object($schoolModel) ? $schoolModel->name : $schoolModel['name'];
$cityName = is_object($schoolModel) ? ($schoolModel->city?->name ?? $schoolModel->city) : ($schoolModel['city'] ?? '');
$locality = is_object($schoolModel) ? ($schoolModel->locality_name ?? $schoolModel->locality?->name ?? '') : ($schoolModel['locality'] ?? '');
@endphp

@section('title', "{$schoolName} - SchoolList")
@section('meta_description', "{$schoolName} in {$locality}, {$cityName}. Check fees, reviews, admission details and contact information.")

@section('content')
<!-- Breadcrumb -->
<section class="bg-gray-100 py-4">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav class="flex text-sm text-gray-600">
            <a href="{{ route('home') }}" class="hover:text-blue-600">Home</a>
            <span class="mx-2">/</span>
            <a href="{{ route('schools.index') }}" class="hover:text-blue-600">Cities</a>
            <span class="mx-2">/</span>
            <a href="{{ route('city.show', is_object($schoolModel) ? $schoolModel->city->slug : $schoolModel['city']) }}" class="hover:text-blue-600">{{ $cityName }}</a>
            <span class="mx-2">/</span>
            <span class="text-gray-900">{{ $schoolName }}</span>
        </nav>
    </div>
</section>

<!-- Header -->
<section class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
            <div class="p-6 md:p-8">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 class="text-2xl md:text-3xl font-bold text-gray-900">{{ $schoolName }}</h1>
                        <p class="text-gray-600 mt-1">
                            {{ $locality }}{{ $locality && $cityName ? ', ' : '' }}{{ $cityName }}
                        </p>
                        
                        <!-- Badges -->
                        <div class="flex flex-wrap gap-2 mt-3">
                            @if(is_object($schoolModel) ? $schoolModel->board : ($schoolModel['board'] ?? ''))
                                <span class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
                                    {{ is_object($schoolModel) ? $schoolModel->board : $schoolModel['board'] }}
                                </span>
                            @endif
                            @if(is_object($schoolModel) ? $schoolModel->school_type : ($schoolModel['school_type'] ?? ''))
                                <span class="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">
                                    {{ is_object($schoolModel) ? $schoolModel->school_type : $schoolModel['school_type'] }}
                                </span>
                            @endif
                            @if((is_object($schoolModel) ? $schoolModel->rating : ($schoolModel['rating'] ?? 0)) > 0)
                                <span class="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-sm flex items-center">
                                    <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                                    </svg>
                                    {{ is_object($schoolModel) ? $schoolModel->rating : $schoolModel['rating'] }}
                                    ({{ is_object($schoolModel) ? $schoolModel->reviews_count : ($schoolModel['reviews_count'] ?? 0) }} reviews)
                                </span>
                            @endif
                        </div>
                    </div>
                    
                    <!-- Contact Button -->
                    <a href="{{ route('inquiry.create', [
                        'city' => is_object($schoolModel) ? $schoolModel->city->slug : $schoolModel['city'],
                        'school' => is_object($schoolModel) ? $schoolModel->slug : $schoolModel['slug']
                    ]) }}" 
                       class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition font-medium">
                        Get Admission Info
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Details -->
<section class="pb-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Main Info -->
            <div class="lg:col-span-2 space-y-6">
                <!-- Overview -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4">Overview</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        @if(is_object($schoolModel) ? $schoolModel->address : ($schoolModel['address'] ?? ''))
                            <div>
                                <h3 class="text-sm font-medium text-gray-500">Address</h3>
                                <p class="text-gray-900">{{ is_object($schoolModel) ? $schoolModel->address : $schoolModel['address'] }}</p>
                            </div>
                        @endif
                        
                        @if(is_object($schoolModel) ? $schoolModel->established : ($schoolModel['established'] ?? ''))
                            <div>
                                <h3 class="text-sm font-medium text-gray-500">Established</h3>
                                <p class="text-gray-900">{{ is_object($schoolModel) ? $schoolModel->established : $schoolModel['established'] }}</p>
                            </div>
                        @endif
                        
                        @if(is_object($schoolModel) ? $schoolModel->grades : ($schoolModel['grades'] ?? ''))
                            <div>
                                <h3 class="text-sm font-medium text-gray-500">Grades</h3>
                                <p class="text-gray-900">{{ is_object($schoolModel) ? $schoolModel->grades : $schoolModel['grades'] }}</p>
                            </div>
                        @endif
                        
                        @if(is_object($schoolModel) ? $schoolModel->medium : ($schoolModel['medium'] ?? ''))
                            <div>
                                <h3 class="text-sm font-medium text-gray-500">Medium</h3>
                                <p class="text-gray-900">{{ is_object($schoolModel) ? $schoolModel->medium : $schoolModel['medium'] }}</p>
                            </div>
                        @endif
                    </div>
                </div>

                <!-- Fees -->
                @if((is_object($schoolModel) ? $schoolModel->fees_min : ($schoolModel['fees_min'] ?? null)) || (is_object($schoolModel) ? $schoolModel->fees_max : ($schoolModel['fees_max'] ?? null)))
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-xl font-semibold mb-4">Fee Structure</h2>
                        <p class="text-2xl font-bold text-blue-600">
                            @if((is_object($schoolModel) ? $schoolModel->fees_min : $schoolModel['fees_min']) && (is_object($schoolModel) ? $schoolModel->fees_max : $schoolModel['fees_max']))
                                ₹{{ number_format(is_object($schoolModel) ? $schoolModel->fees_min : $schoolModel['fees_min']) }} - ₹{{ number_format(is_object($schoolModel) ? $schoolModel->fees_max : $schoolModel['fees_max']) }}
                            @elseif(is_object($schoolModel) ? $schoolModel->fees_min : ($schoolModel['fees_min'] ?? null))
                                ₹{{ number_format(is_object($schoolModel) ? $schoolModel->fees_min : $schoolModel['fees_min']) }}+
                            @else
                                Up to ₹{{ number_format(is_object($schoolModel) ? $schoolModel->fees_max : $schoolModel['fees_max']) }}
                            @endif
                            <span class="text-sm font-normal text-gray-500">/ year</span>
                        </p>
                        @if(is_object($schoolModel) ? $schoolModel->fees_text : ($schoolModel['fees_text'] ?? ''))
                            <p class="text-gray-600 mt-2">{{ is_object($schoolModel) ? $schoolModel->fees_text : $schoolModel['fees_text'] }}</p>
                        @endif
                    </div>
                @endif

                <!-- Facilities -->
                @php
                    $facilities = is_object($schoolModel) && method_exists($schoolModel, 'facilities') 
                        ? $schoolModel->facilities 
                        : (is_object($schoolModel) ? ($schoolModel->facilities ?? []) : ($schoolModel['facilities'] ?? []));
                @endphp
                @if(!empty($facilities) && (is_array($facilities) || is_object($facilities)) && count($facilities) > 0)
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h2 class="text-xl font-semibold mb-4">Facilities</h2>
                        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                            @foreach($facilities as $facility)
                                <div class="flex items-center text-gray-700">
                                    <svg class="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                    {{ is_object($facility) ? $facility->name : (is_array($facility) ? ($facility['name'] ?? $facility) : $facility) }}
                                </div>
                            @endforeach
                        </div>
                    </div>
                @endif
            </div>

            <!-- Sidebar -->
            <aside class="space-y-6">
                <!-- Contact Info -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="font-semibold mb-4">Contact Information</h3>
                    
                    @if(is_object($schoolModel) ? $schoolModel->phone : ($schoolModel['phone'] ?? ''))
                        <div class="flex items-center mb-3">
                            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                            </svg>
                            <a href="tel:{{ is_object($schoolModel) ? $schoolModel->phone : $schoolModel['phone'] }}" class="text-blue-600 hover:underline">
                                {{ is_object($schoolModel) ? $schoolModel->phone : $schoolModel['phone'] }}
                            </a>
                        </div>
                    @endif
                    
                    @if(is_object($schoolModel) ? $schoolModel->email : ($schoolModel['email'] ?? ''))
                        <div class="flex items-center mb-3">
                            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                            <a href="mailto:{{ is_object($schoolModel) ? $schoolModel->email : $schoolModel['email'] }}" class="text-blue-600 hover:underline">
                                {{ is_object($schoolModel) ? $schoolModel->email : $schoolModel['email'] }}
                            </a>
                        </div>
                    @endif
                    
                    @if(is_object($schoolModel) ? $schoolModel->website : ($schoolModel['website'] ?? ''))
                        <div class="flex items-center">
                            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path>
                            </svg>
                            <a href="{{ is_object($schoolModel) ? $schoolModel->website : $schoolModel['website'] }}" target="_blank" class="text-blue-600 hover:underline truncate">
                                Website
                            </a>
                        </div>
                    @endif
                </div>

                <!-- Admission Status -->
                @php
                    $admissionStatus = is_object($schoolModel) ? $schoolModel->admission_status : ($schoolModel['admission_status'] ?? 'unknown');
                @endphp
                @if($admissionStatus !== 'unknown')
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h3 class="font-semibold mb-2">Admission Status</h3>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
                            {{ $admissionStatus === 'open' ? 'bg-green-100 text-green-800' : 
                               ($admissionStatus === 'closed' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800') }}">
                            {{ ucfirst($admissionStatus) }}
                        </span>
                    </div>
                @endif
            </aside>
        </div>
    </div>
</section>

<!-- Related Schools -->
@if(isset($relatedSchools) && $relatedSchools->count() > 0)
<section class="py-12 bg-gray-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-2xl font-bold mb-6">More Schools in {{ $cityName }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            @foreach($relatedSchools as $school)
                @include('components.school-card', ['school' => $school])
            @endforeach
        </div>
    </div>
</section>
@endif
@endsection
