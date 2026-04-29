@extends('layouts.app')

@section('title', $query ? "Search results for '{$query}' - SchoolList" : 'Search Schools - SchoolList')
@section('meta_description', 'Search and filter schools by city, board type, fees, and ratings. Find the best CBSE, ICSE and State Board schools in India.')

@section('content')
<!-- Header -->
<section class="bg-blue-600 text-white py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 class="text-2xl md:text-3xl font-bold">{{ $query ? "Search results for '{$query}'" : 'Search Schools' }}</h1>
    </div>
</section>

<!-- Search & Filters -->
<section class="py-6 bg-gray-100">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <form action="{{ route('search') }}" method="GET" class="bg-white rounded-lg shadow-md p-4">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <!-- Search Input -->
                <div class="md:col-span-2">
                    <input type="text" name="q" placeholder="Search school name..."
                        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        value="{{ $query }}">
                </div>

                <!-- City Filter -->
                <div>
                    <select name="city" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">All Cities</option>
                        @foreach($cities as $c)
                            <option value="{{ $c->slug }}" {{ $city == $c->slug ? 'selected' : '' }}>
                                {{ $c->name }}
                            </option>
                        @endforeach
                    </select>
                </div>

                <!-- Board Filter -->
                <div>
                    <select name="board" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">All Boards</option>
                        @foreach($boards as $b)
                            <option value="{{ $b }}" {{ $board == $b ? 'selected' : '' }}>
                                {{ $b }}
                            </option>
                        @endforeach
                    </select>
                </div>
            </div>

            <div class="mt-4 flex justify-end">
                <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition">
                    Search
                </button>
                @if(request()->hasAny(['q', 'city', 'board', 'type']))
                    <a href="{{ route('search') }}" class="ml-3 text-gray-600 hover:text-gray-800 px-4 py-2">
                        Clear Filters
                    </a>
                @endif
            </div>
        </form>
    </div>
</section>

<!-- Results -->
<section class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        @if($schools->count() > 0)
            <p class="text-gray-600 mb-6">Found {{ $schools->total() }} schools</p>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                @foreach($schools as $school)
                    @include('components.school-card', ['school' => $school])
                @endforeach
            </div>

            <!-- Pagination -->
            <div class="mt-8">
                {{ $schools->links() }}
            </div>
        @else
            <div class="text-center py-12 bg-white rounded-lg shadow">
                <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                <h3 class="text-lg font-medium text-gray-900">No schools found</h3>
                <p class="text-gray-500 mt-1">Try adjusting your search filters</p>
            </div>
        @endif
    </div>
</section>
@endsection
