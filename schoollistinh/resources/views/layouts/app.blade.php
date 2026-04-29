<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'SchoolList - Find Best Schools in India')</title>
    <meta name="description" content="@yield('meta_description', 'Find top schools in India. Search CBSE, ICSE, State Board schools by city, locality, fees, and ratings.')">
    
    @vite(['resources/css/app.css', 'resources/js/app.js'])
</head>
<body class="bg-gray-50 font-sans antialiased">
    @include('layouts.partials.header')
    
    <main>
        @yield('content')
    </main>
    
    @include('layouts.partials.footer')
</body>
</html>
