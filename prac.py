# prospects = [
#     {"name": "John Doe", "status": "contacted", "phone": "555-1234"},
#     {"name": "mary", "status": "new", "phone": "555-5678"},
#     {"name": "Bob Johnson", "status": "contacted", "phone": "555-5678"},
#     {"name": "bill", "status": "new", "phone": "555-5678"},
# ]

# for p in prospects:
#     if p["status"] == "new":
#         print(f"New prospect: {p['name']} - Phone: {p['phone']}")


def filter_by_status(prospects, status):
    return [p for p in prospects if p["status"].lower() == status.lower()]


def add_prospect(prospects, name, status, phone):
    allowed = ["new", "contacted", "follow_up", "closed"]
    if status in allowed:
        prospects.append({"name": name, "status": status, "phone": phone})
        return prospects[-1]
    else:
        # print(f"Invalid status: {status}")
        return None


def update_prospect_staus(prospects, name, new_status):
    allowed = ["new", "contacted", "follow_up", "closed"]
    if new_status not in allowed:
        # print(f"Invalid status: {new_status}")
        return None
    for p in prospects:
        if p["name"].lower() == name.lower():
            p["status"] = new_status
            return p

    # print(f"Prospect not found: {name}")
    return None


def delete_prospect(prospects, name):
    for p in prospects:
        if p["name"].lower() == name.lower():
            prospects.remove(p)
            return
    print(f"Prospect not found: {name}")
    return None


def main():
    prospects = [
        {"name": "John Doe", "status": "contacted", "phone": "555-1234"},
        {"name": "mary", "status": "new", "phone": "555-5678"},
        {"name": "Bob Johnson", "status": "contacted", "phone": "555-5678"},
        {"name": "bill", "status": "new", "phone": "555-5678"},
    ]

    add_prospect1 = add_prospect(prospects, "Alice", "new", "555-9999")
    add_prospect2 = add_prospect(prospects, "Alice", "INVALID", "555-9999")
    # print(f"Added prospect: {add_prospect1}")
    # print(f"Added prospect: {add_prospect2}")

    new_prospect = filter_by_status(prospects, "closed")
    # print(f"New prospects: {new_prospect}")

    update_prospect1 = update_prospect_staus(prospects, "bill", "contacted")
    update_prospect2 = update_prospect_staus(prospects, "BILL", "contacted")
    update_prospect3 = update_prospect_staus(prospects, "nobody", "contacted")

    # print(f"Updated prospect: {update_prospect1}")
    # print(f"Updated prospect: {update_prospect2}")
    # print(f"Updated prospect: {update_prospect3}")

    print("Before:", prospects)
    delete_prospect(prospects, "bill")
    print("After:", prospects)


main()
