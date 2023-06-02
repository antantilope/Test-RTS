
#include <iostream>

#include "base_models.hpp"
#include "uuid.hpp"
#include <string>


using namespace std;

BaseModel::BaseModel() {
    id = uuid::v4();
}

string BaseModel::getId() {
    return id;
}


