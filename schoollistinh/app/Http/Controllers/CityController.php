<?php

namespace App\Http\Controllers;

use App\Models\City;
use App\Repositories\SchoolRepository;
use Illuminate\Http\Request;

class CityController extends Controller
{
    public function show(string $city, Request $request, SchoolRepository $repository)
    {
        // Try database first
        $cityModel = City::where('slug', $city)->first();

        // Fall back to JSON
        if (!$cityModel) {
            $cityData = $repository->getCity($city);
            if (!$cityData) {
                abort(404);
            }
            $cityModel = (object) $cityData;
        }

        $page = $request->get('page', 1);
        $perPage = 20;

        // Get schools - try database first
        if ($cityModel instanceof \App\Models\City) {
            $schoolsQuery = School::active()
                ->where('city_id', $cityModel->id)
                ->with(['locality']);

            // Apply filters
            if ($request->has('board')) {
                $schoolsQuery->byBoard($request->get('board'));
            }
            if ($request->has('type')) {
                $schoolsQuery->byType($request->get('type'));
            }

            $total = $schoolsQuery->count();
            $schools = $schoolsQuery
                ->orderByDesc('is_featured')
                ->orderByDesc('rating')
                ->forPage($page, $perPage)
                ->get();
        } else {
            // Use JSON repository
            $result = $repository->getSchoolsByCity($city, $page, $perPage);
            $schools = $result['schools'];
            $total = $result['total'];
        }

        // Get localities for this city
        $localities = $repository->getLocalitiesInCity($city);

        // Get available boards for filter
        $boards = $schools instanceof \Illuminate\Support\Collection 
            ? $schools->pluck('board')->filter()->unique()->values()
            : collect($schools)->pluck('board')->filter()->unique()->values();

        return view('pages.schools.city', compact(
            'cityModel',
            'schools',
            'localities',
            'boards',
            'total',
            'page',
            'perPage'
        ));
    }
}
