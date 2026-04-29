@extends('layouts.app')

@php
$cityName = is_object($cityModel) ? $cityModel->name : $cityModel['name'];
$citySlug = is_object($cityModel) ? $cityModel->slug : $cityModel['slug'];
@endphp

@section('title', "Schools in {$cityName} - SchoolList")
@section('meta_description', "Find top CBSE, ICSE and State Board schools in {$cityName}. Compare fees, reviews, and admission details.")

@section('content')
<!-- Header -->
<section class="bg-blue-600 text-white py-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 class="text-3xl md:text-4xl font-bold">Schools in {{ $cityName }}</h1>
        <p class="text-blue-100 mt-2">Find the best schools in {{ $cityName }}. {{ number_format($total) }}+ schools listed.</p>
    </div>
</section>

<!-- Filters & Content -->
<section class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col lg:flex-row gap-8">
            <!-- Sidebar Filters -->
            <aside class="w-full lg:w-64 flex-shrink-0">
                <div class="bg-white rounded-lg shadow-md p-4">
                    <h3 class="font-semibold mb-4">Filters</h3>
                    
                    @if($localities->count() > 0)
                        <div class="mb-6">
                            <h4 class="text-sm font-medium text-gray-700 mb-2">Localities</h4>
                            <div class="space-y-1 max-h-48 overflow-y-auto">
                                @foreach($localities as $loc)
                                    <a href="{{ route('locality.show', [$citySlug, $loc['slug']]) }}" 
                                       class="block text-sm text-gray-600 hover:text-blue-600 py-1">
                                        {{ $loc['name'] }} ({{ $loc['school_count'] }})
                                    </a>
                                @endforeach
                            </div>
                        </div>
                    @endif

                    @if($boards->count() > 0)
                        <div class="mb-6">
                            <h4 class="text-sm font-medium text-gray-700 mb-2">Boards</h4>
                            <div class="space-y-1">
                                @foreach($boards as $b)
                                    <a href="{{ route('search', ['city' => $citySlug, 'board' => $b]) }}" 
                                       class="block text-sm text-gray-600 hover:text-blue-600 py-1">
                                        {{ $b }}
                                    </a>
                                @endforeach
                            </div>
                        </div>
                    @endif
                </div>
            </aside>

            <!-- School List -->
            <div class="flex-1">
                @if($schools->count() > 0)
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        @foreach($schools as $school)
                            @include('components.school-card', ['school' => $school])
                        @endforeach
                    </div>

                    <!-- Pagination -->
                    @if($total > $perPage)
                        <div class="mt-8 flex justify-center">
                            <div class="flex space-x-2">
                                @for($i = 1; $i <= ceil($total / $perPage); $i++)
                                    <a href="?page={{ $i }}" 
                                       class="px-4 py-2 rounded {{ $page == $i ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100' }}">
                                        {{ $i }}
                                    </a>
                                @endfor
                            </div>
                        </div>
                    @endif
                @else
                    <div class="text-center py-12 bg-white rounded-lg shadow">
                        <p class="text-gray-500">No schools found in this city.</p>
                    </div>
                @endif
            </div>
        </div>
    </div>
</section>
@endsection
