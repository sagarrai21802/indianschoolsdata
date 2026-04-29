@php
    $schoolData = is_object($school) ? $school : (object) $school;
    $url = is_object($school) && method_exists($school, 'getUrlAttribute') 
        ? $school->url 
        : route('school.show', [
            'city' => $schoolData->city ?? ($schoolData->city_slug ?? 'unknown'),
            'school' => $schoolData->slug
        ]);
@endphp

<div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition">
    <!-- Image -->
    <div class="h-48 bg-gray-200 relative">
        @if(!empty($schoolData->images) && (is_array($schoolData->images) || is_object($schoolData->images)))
            @php $images = is_array($schoolData->images) ? $schoolData->images : json_decode($schoolData->images, true); @endphp
            @if(!empty($images[0]))
                <img src="{{ $images[0] }}" alt="{{ $schoolData->name }}" class="w-full h-full object-cover">
            @else
                <div class="w-full h-full flex items-center justify-center text-gray-400">
                    <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m8-2a2 2 0 00-2-2H9a2 2 0 00-2 2v2m4-2a2 2 0 012-2h2a2 2 0 012 2v2M9 9h6v6H9V9z"></path>
                    </svg>
                </div>
            @endif
        @else
            <div class="w-full h-full flex items-center justify-center text-gray-400">
                <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m8-2a2 2 0 00-2-2H9a2 2 0 00-2 2v2m4-2a2 2 0 012-2h2a2 2 0 012 2v2M9 9h6v6H9V9z"></path>
                </svg>
            </div>
        @endif

        <!-- Featured Badge -->
        @if($schoolData->is_featured ?? false)
            <div class="absolute top-3 left-3 bg-orange-500 text-white text-xs px-2 py-1 rounded">Featured</div>
        @endif

        <!-- Rating Badge -->
        @if($schoolData->rating)
            <div class="absolute top-3 right-3 bg-green-500 text-white text-xs px-2 py-1 rounded flex items-center">
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                </svg>
                {{ $schoolData->rating }}
            </div>
        @endif
    </div>

    <!-- Content -->
    <div class="p-4">
        <h3 class="font-semibold text-gray-900 mb-1 line-clamp-1" title="{{ $schoolData->name }}">
            {{ $schoolData->name }}
        </h3>
        
        <p class="text-sm text-gray-500 mb-2">
            {{ $schoolData->locality_name ?? $schoolData->locality ?? '' }}
            @if($schoolData->city?->name ?? $schoolData->city)
                , {{ $schoolData->city?->name ?? $schoolData->city }}
            @endif
        </p>

        <!-- Board & Type -->
        <div class="flex flex-wrap gap-2 mb-3">
            @if($schoolData->board)
                <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">{{ $schoolData->board }}</span>
            @endif
            @if($schoolData->school_type)
                <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">{{ $schoolData->school_type }}</span>
            @endif
        </div>

        <!-- Fees -->
        @if($schoolData->fees_min || $schoolData->fees_max)
            <p class="text-sm text-gray-600 mb-3">
                <span class="font-medium">Fees:</span>
                @if($schoolData->fees_min && $schoolData->fees_max)
                    ₹{{ number_format($schoolData->fees_min) }} - ₹{{ number_format($schoolData->fees_max) }}
                @elseif($schoolData->fees_min)
                    ₹{{ number_format($schoolData->fees_min) }}+
                @elseif($schoolData->fees_max)
                    Up to ₹{{ number_format($schoolData->fees_max) }}
                @endif
            </p>
        @endif

        <!-- CTA -->
        <a href="{{ $url }}" class="block w-full text-center bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition text-sm font-medium">
            View Details
        </a>
    </div>
</div>
