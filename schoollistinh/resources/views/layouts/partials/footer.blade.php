<footer class="bg-gray-900 text-white mt-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
            <!-- Brand -->
            <div class="col-span-1 md:col-span-1">
                <h3 class="text-xl font-bold mb-4">SchoolList</h3>
                <p class="text-gray-400 text-sm">
                    Find the best schools in India. Comprehensive directory of CBSE, ICSE, and State Board schools.
                </p>
            </div>

            <!-- Quick Links -->
            <div>
                <h4 class="font-semibold mb-4">Quick Links</h4>
                <ul class="space-y-2 text-gray-400 text-sm">
                    <li><a href="{{ route('home') }}" class="hover:text-white">Home</a></li>
                    <li><a href="{{ route('schools.index') }}" class="hover:text-white">All Cities</a></li>
                    <li><a href="{{ route('search') }}" class="hover:text-white">Search</a></li>
                </ul>
            </div>

            <!-- Popular Cities -->
            <div>
                <h4 class="font-semibold mb-4">Popular Cities</h4>
                <ul class="space-y-2 text-gray-400 text-sm">
                    <li><a href="{{ route('city.show', 'delhi') }}" class="hover:text-white">Delhi</a></li>
                    <li><a href="{{ route('city.show', 'mumbai') }}" class="hover:text-white">Mumbai</a></li>
                    <li><a href="{{ route('city.show', 'bangalore') }}" class="hover:text-white">Bangalore</a></li>
                    <li><a href="{{ route('city.show', 'hyderabad') }}" class="hover:text-white">Hyderabad</a></li>
                </ul>
            </div>

            <!-- Legal -->
            <div>
                <h4 class="font-semibold mb-4">Legal</h4>
                <ul class="space-y-2 text-gray-400 text-sm">
                    <li><a href="{{ route('about') }}" class="hover:text-white">About Us</a></li>
                    <li><a href="{{ route('contact') }}" class="hover:text-white">Contact</a></li>
                    <li><a href="{{ route('privacy') }}" class="hover:text-white">Privacy Policy</a></li>
                </ul>
            </div>
        </div>

        <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400 text-sm">
            <p>&copy; {{ date('Y') }} SchoolList. All rights reserved.</p>
        </div>
    </div>
</footer>
