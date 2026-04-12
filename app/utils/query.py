from sqlalchemy import select, func, or_, asc, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def paginate_query(
    db: AsyncSession,
    query,
    params,
    searchable_columns: list = None
) -> dict:
    # Determine model (root entity)
    model = query.column_descriptions[0]["entity"]
    pk = getattr(model, "id")

    # Apply search filters
    filtered_query = query
    if params.search and searchable_columns:
        search_term = f"%{str(params.search).strip()}%"
        filters = [col.ilike(search_term) for col in searchable_columns]
        filtered_query = filtered_query.filter(or_(*filters))

    # Count distinct primary keys for total
    ids_subq = filtered_query.with_only_columns(
        pk).order_by(None).distinct().subquery()
    count_query = select(func.count()).select_from(ids_subq)
    total = (await db.execute(count_query)).scalar_one() or 0

    # Sorting
    if params.sort_by:
        sort_col = getattr(model, params.sort_by, None)
        if sort_col is not None:
            filtered_query = filtered_query.order_by(
                asc(sort_col) if params.sort_order == "asc" else desc(sort_col)
            )
        else:
            filtered_query = filtered_query.order_by(
                text(f"{params.sort_by} {params.sort_order.upper()}")
            )

    # Pagination
    offset = (params.page - 1) * params.limit
    filtered_query = filtered_query.offset(offset).limit(params.limit)

    # Execute filtered paginated query
    result = await db.execute(filtered_query)
    results = result.scalars().unique().all()

    total_pages = (total + params.limit -
                   1) // params.limit if params.limit else 0

    return {
        "meta": {
            "total": total,               # full count
            "limit": params.limit,
            "offset": offset,
            "sort_by": params.sort_by,
            "sort_order": params.sort_order,
            "search": params.search,
            "page": params.page,
            "total_pages": total_pages,
            "total_results": total,       # fixed
        },
        "data": results
    }
