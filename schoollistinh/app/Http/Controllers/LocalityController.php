<?php

namespace App\Http\Controllers;

use App\Repositories\SchoolRepository;

class LocalityController extends Controller
{
    public function show(string $city, string $locality, SchoolRepository $repository)
    {
        // Get city data
        $cityData = $repository->getCity($city);
        if (!$cityData) {
            abort(404);
        }

        // Get schools in locality
        $schools = $repository->getSchoolsByLocality($city, $locality);

        if ($schools->isEmpty()) {
            abort(404);
        }

        // Get all localities for sidebar
        $localities = $repository->getLocalitiesInCity($city);

        return view('pages.schools.locality', compact(
            'cityData',
            'locality',
            'schools',
            'localities'
        ));
    }
}
