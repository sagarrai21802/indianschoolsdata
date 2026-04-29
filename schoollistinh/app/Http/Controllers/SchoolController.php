<?php

namespace App\Http\Controllers;

use App\Models\City;
use App\Models\School;
use App\Repositories\SchoolRepository;

class SchoolController extends Controller
{
    public function index(SchoolRepository $repository)
    {
        // Get all cities with school counts
        $cities = City::active()
            ->withSchools()
            ->orderByDesc('school_count')
            ->get();

        // If database is empty, use JSON repository
        if ($cities->isEmpty()) {
            $cities = $repository->getCities()->map(fn ($city) => (object) $city);
        }

        return view('pages.schools.index', compact('cities'));
    }

    public function show(string $city, string $school, SchoolRepository $repository)
    {
        // Try database first
        $schoolModel = School::with(['city', 'locality', 'facilities'])
            ->where('slug', $school)
            ->whereHas('city', fn ($q) => $q->where('slug', $city))
            ->first();

        // Fall back to JSON repository
        if (!$schoolModel) {
            $schoolData = $repository->getSchool($city, $school);
            
            if (!$schoolData) {
                abort(404);
            }

            // Convert to object for view compatibility
            $schoolModel = (object) $schoolData;
        }

        // Get related schools in same city
        $relatedSchools = School::active()
            ->whereHas('city', fn ($q) => $q->where('slug', $city))
            ->where('id', '!=', is_object($schoolModel) && isset($schoolModel->id) ? $schoolModel->id : 0)
            ->inRandomOrder()
            ->limit(4)
            ->get();

        return view('pages.school.show', compact('schoolModel', 'relatedSchools'));
    }
}
