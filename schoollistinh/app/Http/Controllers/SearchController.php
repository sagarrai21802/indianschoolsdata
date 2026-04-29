<?php

namespace App\Http\Controllers;

use App\Models\City;
use App\Models\School;
use App\Repositories\SchoolRepository;
use Illuminate\Http\Request;

class SearchController extends Controller
{
    public function index(Request $request, SchoolRepository $repository)
    {
        $query = $request->get('q', '');
        $city = $request->get('city');
        $board = $request->get('board');
        $type = $request->get('type');

        $cities = City::active()->orderBy('name')->get();

        // Try database search first
        $schoolsQuery = School::active()
            ->with(['city', 'locality']);

        if ($query) {
            $schoolsQuery->where(function ($q) use ($query) {
                $q->where('name', 'like', "%{$query}%")
                  ->orWhere('address', 'like', "%{$query}%")
                  ->orWhere('locality_name', 'like', "%{$query}%");
            });
        }

        if ($city) {
            $schoolsQuery->whereHas('city', fn ($q) => $q->where('slug', $city));
        }

        if ($board) {
            $schoolsQuery->byBoard($board);
        }

        if ($type) {
            $schoolsQuery->byType($type);
        }

        $schools = $schoolsQuery
            ->orderByDesc('is_featured')
            ->orderByDesc('rating')
            ->paginate(20)
            ->withQueryString();

        // If no results from DB, fall back to repository
        if ($schools->isEmpty() && ($query || $city)) {
            $filters = array_filter([
                'board' => $board,
                'type' => $type,
            ]);
            
            $repoResults = $repository->searchSchools($query, $city, $filters);
            
            // Convert to pagination-like format
            $schools = new \Illuminate\Pagination\LengthAwarePaginator(
                $repoResults->forPage(1, 20),
                $repoResults->count(),
                20,
                1,
                ['path' => $request->url(), 'query' => $request->query()]
            );
        }

        // Get filter options
        $boards = School::active()
            ->whereNotNull('board')
            ->distinct()
            ->pluck('board')
            ->sort();

        return view('pages.search', compact(
            'query',
            'schools',
            'cities',
            'boards',
            'city',
            'board',
            'type'
        ));
    }
}
