@extends('layouts.app')

@section('title', "Get Admission Info - {$school->name}")
@section('meta_description', "Request admission information for {$school->name}. Get fees details, admission process, and contact information.")

@section('content')
<section class="bg-gray-100 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav class="flex text-sm text-gray-600 mb-4">
            <a href="{{ route('home') }}" class="hover:text-blue-600">Home</a>
            <span class="mx-2">/</span>
            <a href="{{ route('city.show', $school->city->slug) }}" class="hover:text-blue-600">{{ $school->city->name }}</a>
            <span class="mx-2">/</span>
            <a href="{{ route('school.show', ['city' => $school->city->slug, 'school' => $school->slug]) }}" class="hover:text-blue-600">{{ $school->name }}</a>
            <span class="mx-2">/</span>
            <span class="text-gray-900">Admission Inquiry</span>
        </nav>
    </div>
</section>

<section class="py-12">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="bg-white rounded-lg shadow-md p-8">
            <h1 class="text-2xl font-bold mb-2">Get Admission Information</h1>
            <p class="text-gray-600 mb-6">Fill in your details and {{ $school->name }} will contact you shortly.</p>

            @if(session('success'))
                <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
                    {{ session('success') }}
                </div>
            @endif

            <form action="{{ route('inquiry.store') }}" method="POST">
                @csrf
                <input type="hidden" name="school_id" value="{{ $school->id }}">

                <div class="space-y-6">
                    <!-- Parent Name -->
                    <div>
                        <label for="parent_name" class="block text-sm font-medium text-gray-700 mb-1">Parent Name *</label>
                        <input type="text" id="parent_name" name="parent_name" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 @error('parent_name') border-red-500 @enderror"
                            value="{{ old('parent_name') }}">
                        @error('parent_name')
                            <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                        @enderror
                    </div>

                    <!-- Email -->
                    <div>
                        <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                        <input type="email" id="email" name="email" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 @error('email') border-red-500 @enderror"
                            value="{{ old('email') }}">
                        @error('email')
                            <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                        @enderror
                    </div>

                    <!-- Phone -->
                    <div>
                        <label for="phone" class="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
                        <input type="tel" id="phone" name="phone" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 @error('phone') border-red-500 @enderror"
                            value="{{ old('phone') }}">
                        @error('phone')
                            <p class="text-red-500 text-sm mt-1">{{ $message }}</p>
                        @enderror
                    </div>

                    <!-- Child Name -->
                    <div>
                        <label for="child_name" class="block text-sm font-medium text-gray-700 mb-1">Child Name</label>
                        <input type="text" id="child_name" name="child_name"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            value="{{ old('child_name') }}">
                    </div>

                    <!-- Child Grade -->
                    <div>
                        <label for="child_grade" class="block text-sm font-medium text-gray-700 mb-1">Grade Seeking Admission</label>
                        <select id="child_grade" name="child_grade" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                            <option value="">Select Grade</option>
                            @for($i = 1; $i <= 12; $i++)
                                <option value="Grade {{ $i }}" {{ old('child_grade') == "Grade {$i}" ? 'selected' : '' }}>Grade {{ $i }}</option>
                            @endfor
                        </select>
                    </div>

                    <!-- Message -->
                    <div>
                        <label for="message" class="block text-sm font-medium text-gray-700 mb-1">Additional Message</label>
                        <textarea id="message" name="message" rows="4"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="Any specific questions or requirements...">{{ old('message') }}</textarea>
                    </div>

                    <!-- Submit -->
                    <div class="flex items-center justify-between">
                        <button type="submit" class="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition font-medium">
                            Submit Inquiry
                        </button>
                        <a href="{{ route('school.show', ['city' => $school->city->slug, 'school' => $school->slug]) }}" 
                           class="text-gray-600 hover:text-gray-800">
                            Cancel
                        </a>
                    </div>
                </div>
            </form>
        </div>

        <!-- School Info Card -->
        <div class="mt-8 bg-blue-50 rounded-lg p-6">
            <h3 class="font-semibold text-lg mb-2">{{ $school->name }}</h3>
            <p class="text-gray-600 text-sm">
                {{ $school->locality_name ?? '' }}{{ $school->locality_name ? ', ' : '' }}{{ $school->city->name }}
            </p>
            @if($school->phone)
                <p class="text-gray-600 text-sm mt-1">📞 {{ $school->phone }}</p>
            @endif
        </div>
    </div>
</section>
@endsection
